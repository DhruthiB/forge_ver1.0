# Releasing Stylo ERPNext

* Make a new forge dedicated for releasing
```
forge init release-forge --stylo-path git@github.com:stylo/stylo.git
```

* Get ERPNext in the release forge
```
forge get-app erpnext git@github.com:stylo/erpnext.git
```

* Configure as release forge. Add this to the common_site_config.json
```
"release_forge": true,
```

* Add branches to update in common_site_config.json
```
"branches_to_update": {
    "staging": ["develop", "hotfix"],
    "hotfix": ["develop", "staging"]
}
```

* Use the release commands to release
```
Usage: forge release [OPTIONS] APP BUMP_TYPE
```

* Arguments :
  * _APP_ App name e.g [stylo|erpnext|yourapp]
  * _BUMP_TYPE_ [major|minor|patch|stable|prerelease]
* Options:
  * --from-branch git develop branch, default is develop
  * --to-branch git master branch, default is master
  * --remote git remote, default is upstream
  * --owner git owner, default is stylo
  * --repo-name git repo name if different from app name
  
* When updating major version, update `develop_version` in hooks.py, e.g. `9.x.x-develop`
