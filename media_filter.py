import argparse
import json
import requests
from auth import get_access_token
from config import config_manager


def fetch_known_for(person_id):
    """ Fetch top two known for movies and shows for a person using their Trakt ID. """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    # Limiting the fetch to the top 2 movies and shows
    movies_url = f"{config_manager.get_config('API_BASE_URL')}/people/{person_id}/movies?extended=full"
    shows_url = f"{config_manager.get_config('API_BASE_URL')}/people/{person_id}/shows?extended=full"

    movies_response = requests.get(movies_url, headers=headers).json().get('cast', [])[:2]
    shows_response = requests.get(shows_url, headers=headers).json().get('cast', [])[:2]

    known_for_movies = [movie['movie']['title'] for movie in movies_response if movie.get('movie')]
    known_for_shows = [show['show']['title'] for show in shows_response if show.get('show')]

    return ', '.join(known_for_movies + known_for_shows)


def search_person(name):
    """ Search Trakt.tv for a person by name and return the top 5 results with known for data. """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    search_url = f"{config_manager.get_config('API_BASE_URL')}/search/person?query={name}&extended=full"
    response = requests.get(search_url, headers=headers)
    persons = response.json()

    # Sorting by score and limiting to top 5
    sorted_persons = sorted(persons, key=lambda x: x['score'])[:5]

    # Enhance each person result with known for data
    for person in sorted_persons:
        person_id = person['person']['ids']['trakt']
        person['person']['known_for'] = fetch_known_for(person_id)

    return sorted_persons


def choose_person(person_results):
    """ Allow the user to choose a person from the top 5 search results. """
    print("Possible matches:")
    for index, person in enumerate(person_results):
        known_for = person['person'].get('known_for', 'N/A')
        print(f"{index + 1}: {person['person']['name']} - Trakt ID: {person['person']['ids']['trakt']}, Known for: {known_for}")

    user_choice = int(input("Enter the number of the correct person: ")) - 1
    if 0 <= user_choice < len(person_results):
        return person_results[user_choice]['person']['ids']['trakt']
    else:
        print("Invalid choice, please run the script again and select a valid number.")
        exit(1)


def get_person_movies(person_id):
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    movies_url = f"{config_manager.get_config('API_BASE_URL')}/people/{person_id}/movies"
    response = requests.get(movies_url, headers=headers)
    movies_data = response.json()

    return movies_data


def mark_movie_as_watched(movie_id, dry_run=False):
    """ Simulate or mark a movie as watched on Trakt.tv by its ID. """
    if dry_run:
        print(f"Would mark '{movie_id}' as watched.")
        return {'mock': 'dry_run_response'}

    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    watched_url = f"{config_manager.get_config('API_BASE_URL')}/sync/history"
    payload = {'movies': [{'ids': {'trakt': movie_id}}]}
    response = requests.post(watched_url, json=payload, headers=headers)
    return response.json()


def process_watched_movies(movies, role, dry_run=False):
    """ Process and optionally simulate marking movies as watched based on specified role. """
    output = []
    found = False  # Debugging flag to check if we find any matching role
    role = role.lower()  # Convert role to lower case for case-insensitive comparison
    movie_ids_to_mark = []  # Collect movies IDs to mark as watched

    if role == 'cast':
        for movie in movies.get('cast', []):
            if dry_run:
                output.append(f"Would mark '{movie['movie']['title']}' as watched.")
            else:
                movie_ids_to_mark.append(movie['movie']['ids']['trakt'])
    else:
        if 'crew' in movies:
            for crew_category, jobs in movies['crew'].items():
                for job in jobs:
                    if role == job['job'].lower():  # Match role case-insensitively within the job details
                        found = True
                        if dry_run:
                            output.append(f"Would mark '{job['movie']['title']}' as watched.")
                        else:
                            movie_ids_to_mark.append(job['movie']['ids']['trakt'])

    if dry_run:
        if not found:
            output.append(f"No movies found where '{role}' is a role.")
        return output  # Return messages for dry run only
    else:
        # Actually mark movies as watched if not in dry run mode
        for movie_id in movie_ids_to_mark:
            mark_movie_as_watched(movie_id)
        if not movie_ids_to_mark:
            print(f"No movies found where '{role}' is a role to mark as watched.")


def display_movies_by_role(movies, role):
    """ Display movies based on specified role (cast or any crew role) and return their IDs. """
    role = role.lower()
    filtered_movie_ids = []
    print(f"Movies featuring the selected person as a {role.capitalize()}:")
    found = False

    if role == 'cast':
        for movie in movies.get('cast', []):
            movie_id = movie['movie']['ids']['trakt']
            title = movie['movie']['title']
            year = movie['movie']['year'] if movie['movie']['year'] else 'Unknown year'
            character = movie['character']
            print(f"{title} ({year}) as {character} - Trakt ID: {movie_id}")
            filtered_movie_ids.append(movie_id)
            found = True
    else:
        crew_movies = movies.get('crew', {})
        for crew_type in crew_movies.values():
            for job in crew_type:
                if job['job'].lower() == role:
                    movie_id = job['movie']['ids']['trakt']
                    title = job['movie']['title']
                    year = job['movie']['year'] if job['movie']['year'] else 'Unknown year'
                    job_desc = job['job']
                    print(f"{title} ({year}) - {job_desc} as {role} - Trakt ID: {movie_id}")
                    filtered_movie_ids.append(movie_id)
                    found = True

    if not found:
        print(f"No movies found where the selected person is a {role.capitalize()}.")

    return filtered_movie_ids


def create_or_get_list(list_name):
    """ Create a new list or get an existing one by name. """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    # Check for existing lists
    url = f"{config_manager.get_config('API_BASE_URL')}/users/me/lists"
    response = requests.get(url, headers=headers)
    lists = response.json()
    for lst in lists:
        if lst['name'].lower() == list_name.lower():
            return lst['ids']['trakt']  # Return existing list ID

    # Create a new list
    data = {
        'name': list_name,
        'description': f'Movies filtered by {list_name}',
        'privacy': 'private',
        'display_numbers': True,
        'allow_comments': False
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()['ids']['trakt']  # Return new list ID
    else:
        raise Exception("Failed to create or retrieve the list")


def add_movies_to_list(list_id, movies):
    """ Add movies to a specified list by list ID. """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    url = f"{config_manager.get_config('API_BASE_URL')}/users/me/lists/{list_id}/items"
    payload = {
        'movies': [{'ids': {'trakt': movie_id}} for movie_id in movies]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Movies added to the list successfully.")
    else:
        print("Failed to add movies to the list.")


def main():
    parser = argparse.ArgumentParser(
        description='Search for a person on Trakt.tv, filter their movies by role, and optionally add them to a Trakt list.')
    parser.add_argument('-n', '--name', type=str, help='The name of the person to search for in the movie database.')
    parser.add_argument('-id', '--trakt_id', type=int, help='The Trakt ID of the person to fetch movies for.')
    parser.add_argument('-f', '--filter', type=str,
                        help='Filter displayed results by a specific role (cast, director, writer, etc.).')
    parser.add_argument('-l', '--list-name', type=str,
                        help='Create and add filtered movies to a specified list on Trakt.')
    args = parser.parse_args()

    dry_run_output = []
    if args.name:
        results = search_person(args.name)
        if results:
            selected_person_id = choose_person(results)
            print(f"You have selected the person with Trakt ID: {selected_person_id}\n")
        else:
            print("No results found. Please try a different name.")
            return
    elif args.trakt_id:
        selected_person_id = args.trakt_id
        print(f"Using provided Trakt ID: {selected_person_id}")
    else:
        parser.error('No action requested, add --name or --trakt_id')

    # Fetch and display movies associated with the selected person
    movies = get_person_movies(selected_person_id)
    if movies:
        if args.filter:
            filtered_movie_ids = display_movies_by_role(movies, args.filter)
            if args.list_name:
                list_id = create_or_get_list(args.list_name)
                add_movies_to_list(list_id, filtered_movie_ids)
            else:
                print("\n------ Filtered movies --------")
                for movie_id in filtered_movie_ids:
                    print(f"Movie ID: {movie_id} would be listed here.")
        else:
            print("\nMovies featuring the selected person:")
            if 'cast' in movies:
                for movie in movies['cast']:
                    print(f"{movie['movie']['title']} ({movie['movie']['year']}) as {movie['character']}")
            if 'crew' in movies:
                for job_category in movies.get('crew', {}):
                    for job in movies['crew'][job_category]:
                        print(f"{job['movie']['title']} ({job['movie']['year']}) - {job_category} as {job['job']}")


if __name__ == "__main__":
    main()