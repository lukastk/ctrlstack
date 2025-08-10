# Create a worktree for docs branch in a temp folder
random_dir="/tmp/dir_$(openssl rand -hex 8)"
git worktree add "$random_dir" docs

# Generate docs into the temp folder
nbl render-docs -o "$random_dir"

# Commit and push to docs branch
cd "$random_dir"
git add --all
git commit -m "Update docs"
git push origin docs

# Remove the worktree (and delete the temp folder)
cd -
git worktree remove "$random_dir"
rm -rf "$random_dir"