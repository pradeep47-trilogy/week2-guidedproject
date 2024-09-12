import os
import base64
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

def format_data_for_openai(diffs, readme_content, commit_messages):
    prompt = None

    # Combine the changes into a string with clear delineation.
    changes = "\n\n".join(
        [f'File: {file["filename"]} \nDiff: \n{file["patch"]}\n' for file in diffs]
    )

    # Combine all commit messages
    messages = "\n".join(commit_messages.split) + "\n\n"

    # Decode the README content
    readme = base64.b64decode(readme_content.content).decode("UTF-8")

    # Construct the prompt with clear instructions for the LLM.
    prompt = ("Please review the following code changes and commit messages from a Github pull request:\n"
              "Code changes from Pull Request:\n"
              f"{changes}\n"
              "Commit Messages:\n"
              f"{messages}\n"
              "Here is the current README file content:\n"
              f"{readme}\n"
              "Consider the codes changes from the pull request (including changes in docstrings and other metadata), and the commit messages. Determine if the README needs to be updated. If so, edit the README, ensuring to maintain its existing style and clarity.\n"
              "Update README: \n")
              

    return prompt

def call_openai(prompt: str) -> str:
    """Send the prompt to OpenAI, return the response"""
    client = ChatOpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    try:
        messages = [
            {
                "role": "system",
                "content": "You are an AI trained to help with updating README files based on code changes.",
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Call openAI
        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)

        return content
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None

def update_readme_and_create_pr(repo: str, updated_readme: str, readme_sha: str):
    """Submit updated README content as a PR in a new branch"""
    
    commit_message = "Propose README update based on the recent code changes"
    main_branch = repo.get_branch("main")
    new_branch_name = f"update_readme-{readme_sha[:10]}"
    new_branch = repo.create_git_ref(
        ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha
    )

    # Update README file
    repo.update_file(
        path="README.md",
        message=commit_message,
        content=updated_readme,
        sha=readme_sha,
        branch=new_branch_name,
    )

    # Create a PR
    pr_title = "Update README based on recent changes"
    pr_body = "This pr proposes an update to the README based on recent code changes. Please review and merge if appropriate"
    pull_request = repo.create_pull(
        title = pr_title, body=pr_body, head=new_branch_name, base="main"
    )

    return pull_request
    