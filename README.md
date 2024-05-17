# Trakt Media Filter

## Overview

This script allows you to search for people on Trakt.tv, filter movies by their roles (e.g., cast, director, writer), and optionally add them to a Trakt list. It's a great tool for managing movie lists based on specific actor or crew involvement.

## Getting Started

## Prerequisites

Before you begin, ensure you have Python 3.x installed on your system. You will also need to set up a virtual environment and install the required packages:

### Setting Up Python and Virtual Environment

1. **Install Python**:
   - If not already installed, download and install Python from [python.org](https://www.python.org/downloads/).

2. **Create a Virtual Environment**:
   - Open a terminal or command prompt.
   - Navigate to the project directory where you want to set up the virtual environment.
   - Run the following command to create a virtual environment named `env`:
     ```bash
     python -m venv virtenv
     ```

3. **Activate the Virtual Environment**:
   - On Windows, activate the virtual environment by running:
     ```bash
     .\virtenv\Scripts\activate
     ```
   - On macOS or Linux, activate it with:
     ```bash
     source virtenv/bin/activate
     ```

4. **Install Required Packages**:
   - Ensure that the virtual environment is activated.
   - Install the required libraries using pip:
     ```bash
     pip install -r requirements.txt
     ```

### Note

- Remember to activate the virtual environment every time you work on this project. This ensures that you are using the correct Python interpreter and dependencies.

- Deactivate the virtual environment when you are done by running `deactivate` in your terminal or command prompt.


### Trakt.tv API Setup

Before you can use this script, you need to set up an application on Trakt.tv to obtain an API key:

1. **Create a Trakt.tv Account**:
   - Go to [Trakt.tv](https://trakt.tv/) and sign up for an account if you do not already have one.

2. **Register a New API Application**:
   - Navigate to the [Trakt API Applications](https://trakt.tv/oauth/applications) page.
   - Click on "New Application".
   - Fill out the form:
     - **Name**: Your application's name (e.g., My Movie Manager).
     - **Redirect uri**: Use `http://localhost:8000`.
     - **Javascript CORS**: Use `http://localhost`
     - **Permissions**: Request permissions that your application needs.
   - Submit the form to create your application.

3. **Note Your API Keys**:
   - After creating the application, note the `Client ID` and `Client Secret` provided. You will need these for your configuration file.

### Configuration File Setup

Create a `config.json` file in the same directory as your script with the following content:

```json
{
    "CLIENT_ID": "your_trakt_client_id_here",
    "CLIENT_SECRET": "your_trakt_client_secret_here",
    "API_BASE_URL": "https://api.trakt.tv"
}
```

Replace `your_trakt_client_id_here` and `your_trakt_client_secret_here` with the credentials obtained from your Trakt application.

## Usage

To run the script, you can use the following command-line arguments:

- `-n`, `--name`: Name of the person to search for.
- `-id`, `--trakt_id`: Directly use the Trakt ID of the person to fetch movies for.
- `-f`, `--filter`: Filter displayed results by a specific role (e.g., cast, director, writer).
- `-l`, `--list-name`: Specify a list name to create and add filtered movies to this list on Trakt.

### Examples

**Search by Name and Display All Movies:**
```bash
python media_filter.py -n "Donald Glover"
```

**Filter Movies by Role:**
```bash
python media_filter.py -n "Donald Glover" -f "executive producer"
```

**Create a List and Add Filtered Movies:**
```bash
python media_filter.py -n "Donald Glover" -f director -l "Donald Glover Directors"
```

### Troubleshooting
If you encounter issues related to API permissions or connectivity, ensure your config.json file is correctly set up with valid API keys and that your network settings allow requests to Trakt.tv.
