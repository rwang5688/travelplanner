# Code Server Node 22 Upgrade

## Summary

Upgrade the code-server CloudFormation template (`code-server/code-server.yaml`) from Node.js 20.18.0 to Node 22 LTS to resolve the JSII/CDK deprecation warning that blocks clean `cdk deploy` runs.

## Context

- Node 20 reached EOL on 2026-04-30
- CDK will drop Node 20 support entirely after 2026-10-30
- The warning is emitted by JSII (underlying CDK synthesis engine)
- The instance is ARM64 (c7g.xlarge, aarch64)
- Node is installed via direct binary tarball to `/usr/local/` (no nvm, no apt repo)

## Current State (InstallNode step in SSM doc)

```yaml
- NODE_VERSION="20.18.0"
- ARCH=$(uname -m)
- if [ "$ARCH" = "aarch64" ]; then NODE_ARCH="arm64"; else NODE_ARCH="x64"; fi
- cd /tmp
- curl -fL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz" -o node.tar.xz
- tar -xf node.tar.xz
- cp -r node-v${NODE_VERSION}-linux-${NODE_ARCH}/* /usr/local/
- rm -rf node-v${NODE_VERSION}-linux-${NODE_ARCH} node.tar.xz
```

## Required Changes

### 1. Update InstallNode step

Change `NODE_VERSION="20.18.0"` to `NODE_VERSION="22.16.0"` (or latest 22.x LTS).

### 2. Update SSM document parameter allowedValues

The `nodeVersion` parameter currently allows:
- node_21.x
- node_20.x
- node_19.x

Update to include `node_22.x` and optionally remove deprecated versions.

### 3. Update the SSM document parameter default

Change `default: node_20.x` to `default: node_22.x`.

## Immediate Workaround (running instance)

Run this on the live code-server to upgrade in-place without redeploying the stack:

```bash
NODE_VERSION="22.16.0"
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then NODE_ARCH="arm64"; else NODE_ARCH="x64"; fi
cd /tmp
curl -fL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz" -o node.tar.xz
tar -xf node.tar.xz
sudo cp -r node-v${NODE_VERSION}-linux-${NODE_ARCH}/* /usr/local/
rm -rf node-v${NODE_VERSION}-linux-${NODE_ARCH} node.tar.xz
node --version
```

## File Location

- Template: `code-server/code-server.yaml`

## Risk Assessment

- Low risk: same install method, just a version bump
- No package manager conflicts (no apt/nvm involved)
- Only affects the Node binary in `/usr/local/`
- Global npm packages (aws-cdk) will need a reinstall after upgrade: `npm install -g aws-cdk`
