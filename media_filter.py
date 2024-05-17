import argparse
import time
import requests
from auth import get_access_token
from config import config_manager


def fetch_known_for(person_id):
    """Fetch all movies and shows for a person and prepare a concise known for section."""
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    # Fetching both movies and shows
    movies_url = f"{config_manager.get_config('API_BASE_URL')}/people/{person_id}/movies?extended=full"
    shows_url = f"{config_manager.get_config('API_BASE_URL')}/people/{person_id}/shows?extended=full"

    # Handle API requests safely
    try:
        movies_response = requests.get(movies_url, headers=headers).json().get('cast', [])
        shows_response = requests.get(shows_url, headers=headers).json().get('cast', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {str(e)}")
        return "Data fetch error"

    # Combine movies and shows into one list and sort/format them
    combined_media = movies_response + shows_response
    return get_known_for_titles(combined_media)


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

    # Filter to ensure only person type results are processed
    filtered_persons = []
    for person in persons:
        if 'person' in person:
            filtered_persons.append(person)

    # Enhance each person result with known for data, limit to top 5
    top_persons = []
    for person in filtered_persons[:5]:
        person_id = person['person']['ids']['trakt']
        person['person']['known_for'] = fetch_known_for(person_id)
        top_persons.append(person)

    return top_persons


def choose_person(person_results):
    """ Allow the user to choose a person from the top 5 search results. """
    if not person_results:
        print("No valid data to display.")
        return None

    print("Possible matches:")
    for index, person in enumerate(person_results):
        # Correctly access nested 'person' dictionary
        person_details = person.get('person', {})
        known_for = person_details.get('known_for', 'N/A')
        name = person_details.get('name', 'Unknown')
        trakt_id = person_details.get('ids', {}).get('trakt', 'No ID')

        print(f"{index + 1}: {name} - Trakt ID: {trakt_id}, Known for: {known_for}")

    try:
        user_choice = int(input("\n\nEnter the number of the correct person: ")) - 1
        if 0 <= user_choice < len(person_results):
            return person_results[user_choice]['person']['ids']['trakt']
    except ValueError:
        print("Invalid input. Please enter a valid number.")
    return None


def get_person_movies(person_id):
    """Fetch movies associated with a person and return detailed information."""
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    movies_url = f"{config_manager.get_config('API_BASE_URL')}/people/{person_id}/movies?extended=full"

    response = requests.get(movies_url, headers=headers)
    if response.status_code == 200:
        movies_data = response.json()
        return movies_data
    else:
        print(f"Failed to fetch movies for person ID {person_id}: {response.status_code} - {response.text}")
        return None


def get_known_for_titles(media_list):
    """Extract and format titles from the media list to a more readable format."""
    movies = [item['movie'] for item in media_list if 'movie' in item]
    shows = [item['show'] for item in media_list if 'show' in item]

    # Sort by 'votes' which is a common metric for popularity
    sorted_movies = sorted(movies, key=lambda x: x.get('votes', 0), reverse=True)[:2]
    sorted_shows = sorted(shows, key=lambda x: x.get('votes', 0), reverse=True)[:2]

    formatted_titles = [f"{m['title']} ({m.get('year', 'Unknown Year')})" for m in sorted_movies + sorted_shows]
    return ', '.join(formatted_titles) if formatted_titles else "Insufficient data"


def display_movies_by_role(movies, role=None, show_details=False):
    """ Display movies based on specified role (cast or any crew role) and return their IDs, titles, and roles. """
    filtered_movies = []
    found = False

    if 'cast' in movies:
        for movie in movies['cast']:
            character = movie.get('character')
            if character:  # Ensure the character name is not empty
                movie_id = movie['movie']['ids']['trakt']
                title = movie['movie']['title']
                year = movie['movie'].get('year', 'No Year Found')  # Handle None year
                if show_details:
                    print(f"{title} ({year if year else 'No Year Found'}) as {character} - Trakt ID: {movie_id}")
                filtered_movies.append({'id': movie_id, 'title': title, 'role': character})
                found = True

    if 'crew' in movies:
        for department, crew_jobs in movies['crew'].items():
            for job in crew_jobs:
                if role is None or job['job'].lower() == role.lower():
                    movie_id = job['movie']['ids']['trakt']
                    title = job['movie']['title']
                    year = job['movie'].get('year', 'No Year Found')
                    job_description = job['job']
                    if show_details:
                        print(f"{title} ({year if year else 'No Year Found'}) - {job_description} as {department} - Trakt ID: {movie_id}")
                    filtered_movies.append({'id': movie_id, 'title': title, 'role': f"{job_description} ({department})"})
                    found = True

    if not found:
        print(f"No movies found where the selected person is involved as '{role if role else 'any role'}'.")

    return filtered_movies


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
    """ Add movies to a specified list by list ID in batches with progress updates. """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    url = f"{config_manager.get_config('API_BASE_URL')}/users/me/lists/{list_id}/items"

    batch_size = 5  # Adjust batch size as needed
    batches = [movies[i:i + batch_size] for i in range(0, len(movies), batch_size)]
    total_batches = len(batches)

    for index, batch in enumerate(batches, start=1):
        payload = {'movies': [{'ids': {'trakt': movie_id}} for movie_id in batch]}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(f"Batch {index}/{total_batches} of movies added to the list successfully.")
        else:
            print(f"Failed to add batch {index}/{total_batches} to the list. Status: {response.status_code}, Message: {response.text}")
            if response.status_code == 429:
                retry_delay = int(response.headers.get('Retry-After', 3))  # Use Retry-After header if available
                print(f"Rate limit hit. Waiting for {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Recursively retry only the failed batch
                add_movies_to_list(list_id, batch)
            else:
                # Break from the loop if a non-retryable error occurs
                break

        # Pause slightly between requests to respect API rate limits
        time.sleep(1)  # Adjust as necessary based on the server's response and policies



def like_list(list_id):
    """ Like a list on Trakt.tv by its ID. """
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_manager.get_config('CLIENT_ID')
    }
    url = f"{config_manager.get_config('API_BASE_URL')}/users/me/lists/{list_id}/like"
    response = requests.post(url, headers=headers)
    if response.status_code == 204:  # Trakt uses 204 No Content for a successful like action
        print("\nList liked successfully.")
    else:
        print(f"Failed to like the list. Status: {response.status_code}, Message: {response.text}")
        if response.status_code == 429:  # Rate limit exceeded
            print("Rate limit hit. Waiting for 2 second...")
            time.sleep(2)
            like_list(list_id)


def main():
    parser = argparse.ArgumentParser(
        description='Search for a person on Trakt.tv, filter their movies by role, and optionally add them to a Trakt list.')
    parser.add_argument('-n', '--name', type=str, help='The name of the person to search for in the movie database.')
    parser.add_argument('-id', '--trakt_id', type=int, help='The Trakt ID of the person to fetch movies for.')
    parser.add_argument('-f', '--filter', type=str,
                        help='Filter displayed results by a specific role (cast, director, writer, etc.).',
                        default=None)
    parser.add_argument('-l', '--list-name', type=str,
                        help='Create and add filtered movies to a specified list on Trakt.')

    args = parser.parse_args()

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
        parser.error('No action requested, add --name or --trakt_id to perform a search.')

    movies = get_person_movies(selected_person_id)
    if movies:
        filtered_movies = display_movies_by_role(movies, args.filter, show_details=bool(args.list_name))
        if args.list_name:
            list_id = create_or_get_list(args.list_name)
            time.sleep(2)
            like_list(list_id)
            time.sleep(2)
            add_movies_to_list(list_id, [movie['id'] for movie in filtered_movies])
        else:
            print("\n------ Filtered movies --------")
            for movie in filtered_movies:
                print(f"{movie['title']} - Movie ID: {movie['id']} (Role: {movie['role']})")


if __name__ == "__main__":
    main()