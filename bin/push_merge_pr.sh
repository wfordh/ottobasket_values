BRANCH_NAME="chore_automated_pr_yesterday_stats_$(date +%Y-%m-%d)""
PR_TITLE="chore (automated): update yesterday stats"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Creating PR \"$PR_TITLE\" for branch $BRANCH_NAME"
  
  if ! git push origin $BRANCH_NAME; then
    echo "Failed to push branch"
    exit 1
  fi

  gh pr create --head "$BRANCH_NAME" --title "$PR_TITLE" --body "This is an automated PR to add stats from yesterday"
  gh pr merge --auto --delete-branch --squash "$BRANCH_NAME"
else
  echo "Nothing to update...why is that"
fi
