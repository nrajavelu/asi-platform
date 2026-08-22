FROM node:18-slim

WORKDIR /work

# node_modules is pre-built on the HOST (not during `docker build`) and
# copied in as-is - see the "regenerate node_modules" note below. Node
# itself cannot start inside a plain container on this machine's Docker
# Desktop/macOS 12 setup (same fork/thread restriction that needed
# `privileged: true` for Judge0's postgres/redis containers), and `docker
# build` has no equivalent flag, so `RUN npm install` can't run here at all.
#
# To regenerate node_modules after changing package.json (run on the host,
# from this directory - the --os/--cpu/--libc flags force npm to fetch the
# Linux binary for esbuild's native dependency even though npm itself is
# running on macOS):
#   rm -rf node_modules package-lock.json
#   npm install --no-audit --no-fund --os=linux --cpu=x64 --libc=glibc
COPY node_modules /work/node_modules
COPY run-test.js /work/run-test.js

ENTRYPOINT ["node", "/work/run-test.js"]
