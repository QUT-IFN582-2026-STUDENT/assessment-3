# Libraries to Install

Make sure to install the required libraries using the requirements.txt file

Run the following commands before attempting to run this code.

```bash
py -m pip install -r requirements.txt
python3 -m pip install -r requirements.txt
```

# Version Control

See the complete beginner guide, including feature branches, merge conflict resolution, VS Code's Merge Editor, `git mergetool`, and pull requests:

[Git and VS Code Workflow Guide](docs/git-vscode-workflow.html)

## Quick workflow

1. Create or sign in to GitHub using https://github.com/.

2. Download and install Git for Windows from https://git-scm.com/install/windows.

3. Restart VS Code. Open PowerShell, Git Bash, or the VS Code terminal.

4. Configure your Git identity once. Use your GitHub-associated email address:

   ```bash
   git config --global user.name "Your Full Name"
   git config --global user.email "your-email@example.com"
   git config --global user.name
   git config --global user.email
   ```

5. Configure VS Code as Git's merge tool once. In PowerShell, use single quotes around the second command:

   ```powershell
   git config --global merge.tool vscode
   git config --global mergetool.vscode.cmd 'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'
   git config --global mergetool.keepBackup false
   ```

6. Open the parent folder where you keep your course work, then clone the repository:

   ```bash
   cd "C:\Users\<userName>\IFN582"
   git clone https://github.com/Garyn-QUT/ifn582-assessment-3.git
   cd ifn582-assessment-3
   ```

7. Start from the latest `dev` branch:

   ```bash
   git fetch origin
   git switch dev
   git pull --ff-only origin dev
   ```

8. Create a feature branch before making changes:

   ```bash
   git switch -c feature/your-short-description
   ```

9. Make and test your code changes. Review and commit them:

   ```bash
   git status
   git diff
   git add <filename>
   # Or use: git add .
   git diff --staged
   git commit -m "Describe the change"
   ```

10. Push your local feature branch to GitHub:

    ```bash
    git push -u origin feature/your-short-description
    ```

11. Before opening a pull request, merge the latest `dev` into your feature branch:

    ```bash
    git fetch origin
    git switch feature/your-short-description
    git merge origin/dev
    ```

12. If Git reports conflicts, open the conflicted files in VS Code's Source Control view and use the Merge Editor. Choose
    **Accept Current Change**, **Accept Incoming Change**, **Accept Both Changes**, or edit the result manually. Then save,
    stage, and complete the merge:

    ```bash
    git mergetool
    git add <resolved-file>
    git status
    git commit -m "Resolve merge conflict with dev"
    ```

    If you need to cancel an unfinished merge, use `git merge --abort` before committing.

13. Test again and push the updated feature branch:

    ```bash
    git push
    ```

14. On GitHub, create a pull request from `feature/your-short-description` into `dev`. Do not push feature work directly to
    `dev` unless the team explicitly requests it.
