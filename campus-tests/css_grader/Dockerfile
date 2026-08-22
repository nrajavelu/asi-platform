FROM mcr.microsoft.com/playwright:v1.47.0-jammy

WORKDIR /work

# The base image bundles Node + the browsers, but not the `playwright` npm
# package itself as a require()-able module - node_modules is pre-built on
# the HOST (not during `docker build`, for the same reason as
# react_grader/Dockerfile: Node can't start inside a plain container on
# this machine's Docker Desktop/macOS 12 setup, so `RUN npm install` can't
# run here at all). The version pinned in package.json (1.47.0) must match
# this base image tag exactly - the JS driver talks to the browsers that
# were baked in at that version.
#
# To regenerate node_modules after changing package.json (run on the host,
# from this directory):
#   rm -rf node_modules package-lock.json
#   PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --no-audit --no-fund --os=linux --cpu=x64 --libc=glibc
COPY node_modules /work/node_modules
COPY run-css-test.js /work/run-css-test.js

ENTRYPOINT ["node", "/work/run-css-test.js"]
