# JobTread Payroll Category Validation Report

# OVERVIEW
  This is an internal tool for JobTread to identify and categorize labor entries assigned to "Uncategorized Time". It provides a daily timeline for workers and searches company logs for name mentions to help admins reassign hours quickly.

# SENSITIVE DATA WARNING
  DO NOT check your ".env" file into GitHub. It contains your API Grant Key. Ensure your ".gitignore" file includes ".env" before pushing to any repository.

# PREREQUISITES

  Python 3.x
  A JobTread Organization ID and API Grant Key
  Access to a terminal/command line


# LOCAL INSTALLATION (DEBIAN/LINUX)
Step 1: Clone the repository
        bash
        git clone [https://github.com/quiggnasty/bug-free-barnacle.git](https://github.com/quiggnsasty/bug-free-barnacle.git)
        cd bug-free-barnacle



Step 2: Create a Virtual Environment
        python3 -m venv venv
        source venv/bin/activate

Step 3: Install Dependencies
        python3 -m pip install flask requests python-dotenv gunicorn

Step 4: Configure Environment Variables
        Create a file named ".env" in the root folder and add:
                JOBTREAD_GRANT_KEY=your_actual_key_here
                JOBTREAD_ORG_ID=your_org_id_here

Step 5: Run for Development
        python3 app.py

# PRODUCTION DEPLOYMENT

To run this as a persistent service on a server (Debian):

Step 1: Install Gunicorn
        pip install gunicorn

Step 2: Run with Gunicorn (Example)
        gunicorn --workers 3 --bind 0.0.0.0:8080 app:app

Step 3: (Optional) Set up Nginx
        Point an Nginx reverse proxy to port 8080 to handle internal DNS names and SSL.

PROJECT STRUCTURE

        app.py: Main Flask logic and API handlers

        templates/index.html: The dashboard UI

        .env: (Private) API credentials

        requirements.txt: List of python packages
