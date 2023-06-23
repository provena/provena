# Integration Testing

This directory dedicates space for all integration testing to be kept and organised, separate from the unit testing. Where unit tests are designed for testing lower level functionality of our code, meanwhile, the integration tests are purposed for testing user stories. That is, integration tests are high level tests requiring minimal dependency on our source code.

## How to test

1. Open a terminal in tests/integration

2. Create and source a virtual environment using: `python3 -m venv .venv` followed by `source .venv/bin/activate`.

3. Install required packages with `pip install -r requirements.txt`.

4. Specify your python interpreter in vs code by either accepting the prompt raised when you created the virtual environment, or manually by running the "Python: Select interpreter" command from the command palette (ctrl + shift + p) and selecting your virtual environment. If your python extension won't pick up your virtual environment, just reload your window using the "Reload window" command in the command palette, then select the interpreter.

5. Set your environment variables by creating a ".env" file in the integration directory. Its contents should mirror that of "template-env" which is provided in the tests/integration directory. You can copy-paste the contents over. Certain tests require different bot "users" to test group roles and group access rights, these 'bot' users will need to be created in the Keycloak instance and their login details included in the .env file. 

**Warning**: Be careful not to save or push to a public remote any files with these credentials.

6. run `pytest` in your terminal or use the pytest extension which has a nice interface.

**Note**: You can point the integration tests to different (optionally locally) deployed endpoints. However, ensure the set of endpoints all point to the same AWS resources (databases). This is because a dataset may be created using the datastore api, and then searched for using the registry api, or referenced in a provenance document using the provenance api. If the endpoints for the API's point to different AWS resources, the tests may erroneously fail when searching for items.

**Note**: Sometimes the `.env` file isn't picked up. In that case, run `pytest --envfile [your envfile]` to specify which env file to use.

## How to extend tests

### Where to put tests

Create new subdirectories in tests/integration for testing different components. Note that pytest requires your modules and function tests to begin with "test\_".

### Adding dependencies

Append your dependencies to the requirements.txt file. Recall though, that these integration tests are to have little dependency on our source code and are not desired to test lower level functionality.

### Getting valid tokens

To get valid tokens for calling APIs there are a couple tools you can import using `from KeycloakRestUtilities.Token import get_token, BearerAuth`
There is an example use of these in the data-store-api integration tests.

### Pydantic Models
It is highly recommended to use pydantic models for creating payloads and parsing responses as they validate payloads and responses. This is especially useful for testing the registry api, where the responses are often complex and nested. Furthermore, it will enhance the maintainability of the tests as models are iterated, preventing the requirement to update tests as much, and making it easier to see where updates may be required if fields are missing (thanks to mypy).