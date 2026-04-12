# Agent-Guard Integration Report

## Installation Summary

✅ **Successfully installed and configured agent-guard v0.1.0**

Agent-guard is a deterministic security interception layer for AI Agents, now protecting the Arduino Tools project.

## Installation Details

### 1. Package Installation
- **Source**: https://github.com/d-wwei/agent-guard
- **Version**: 0.1.0
- **Installation Method**: Built from source, installed globally via npm
- **Installation Path**: `C:\Users\51771\AppData\Roaming\npm\node_modules\agent-guard`

### 2. Claude Code Integration

**Hooks Installed**: ✓
- **PreToolUse Hook**: `agent-guard check` (runs before every tool execution)
- **PostToolUse Hook**: `agent-guard sanitize` (redacts credentials from output)
- **Configuration File**: `C:\Users\51771\.claude\settings.json`
- **Timeout**: 5 seconds per hook

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [{
          "type": "command",
          "command": "agent-guard check",
          "timeout": 5
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [{
          "type": "command",
          "command": "agent-guard sanitize",
          "timeout": 5
        }]
      }
    ]
  }
}
```

### 3. Arduino Tools Project Configuration

**Project Initialized**: ✓
- **Project ID**: 05d8cf553b396d4b
- **Risk Map**: Auto-generated scanning 56 files
- **Risk Levels**:
  - High Sensitivity: 1 file (.env.example)
  - Medium Sensitivity: 55 files (source code)
  - Low Sensitivity: 0 files
- **Trust Level**: 0/2 (zero trust initially)
- **Configuration**: `.agent-guard.yaml` (custom rules in project directory)

## Security Architecture

### 5-Layer Defense System

1. **Hard Rules** (Layer 1)
   - Deterministic whitelists and blacklists
   - File path patterns and command patterns
   - 0.038ms latency per check
   - Examples:
     - Allow: `*/arduino-tools/projects/*/sketch.ino`
     - Deny: `git.*push.*--force`
     - Deny: `.env` file modifications

2. **Path Safety** (Layer 2)
   - File sensitivity classification
   - Risk assessment based on file type
   - Blocks high-risk operations on sensitive files
   - Examples:
     - HIGH: `.env` files, git config
     - MEDIUM: Source code files
     - LOW: Generated artifacts

3. **Trust Evaluation** (Layer 3)
   - Graduated permissions based on history
   - Trust score increases with safe operations
   - Allows risky operations after warm-up
   - Current: Trust Level 0 (requires confirmation for risky ops)

4. **Rate Anomaly** (Layer 4)
   - Detects behavioral anomalies
   - Monitors operation frequency
   - Examples:
     - Wokwi simulation: Max 10 runs per 10 minutes
     - API calls: Max 20 per 5 minutes
   - Prevents runaway loops and excessive API usage

5. **Synthesis** (Layer 5)
   - Credential sanitization
   - Multi-layer consensus before allowing risky actions
   - Automatic redaction of API keys and tokens
   - Patterns:
     - Redact: `api_key`, `token`, `ANTHROPIC_API_KEY`, `MOONSHOT_KEY`, `WOKWI_CLI_TOKEN`
     - Obfuscate: Home directory paths

## Configured Rules

### Safety Rules (`.agent-guard.yaml`)

#### Whitelist Rules
- ✅ Generated code files (sketch.ino, diagram.json, wokwi.toml)
- ✅ Project build artifacts
- ✅ Build commands (cargo, npm, arduino-cli, wokwi-cli)
- ✅ Safe read operations (Read, Glob, Grep)

#### Blacklist Rules
- ❌ Environment files (.env, .env.*)
- ❌ Git force operations (push --force, reset --hard)
- ❌ Root lock files (Cargo.lock, package-lock.json)
- ❌ Recursive deletes (rm -rf, rmdir)

#### Anomaly Detection
- Rate limit: Wokwi simulations (10 runs per 10 minutes)
- Rate limit: API calls (20 calls per 5 minutes)
- Pattern matching for detection

#### Credential Protection
- Auto-redact: API keys, tokens, passwords
- Sanitize: Home directory paths
- Patterns: ANTHROPIC_API_KEY, MOONSHOT_KEY, WOKWI_CLI_TOKEN

## How It Works with Arduino Tools

### Code Generation Phase
1. User provides prompt → invoke LLM
2. **PreToolUse**: agent-guard checks if LLM call is safe
   - Verifies API credentials are protected
   - Checks rate limits (max 20 API calls per 5 min)
   - Layer 5 sanitizes credentials
3. LLM generates code
4. **PostToolUse**: Redacts credentials from response
5. Code written to sketch.ino
   - **PreToolUse**: Checks if write is allowed
   - Verifies file path is in whitelist
   - Allows write to generated code files

### Build & Compilation
1. Runs `cargo build` or `npm build`
2. **PreToolUse**: Checks build command
   - Verifies command pattern matches whitelist
   - Allows standard build operations
3. Build executes
4. **PostToolUse**: Sanitizes build output
   - Redacts any credentials in logs

### Simulation Phase
1. Runs `wokwi-cli` simulation
2. **PreToolUse**: Checks simulation command
   - Allows wokwi-cli execution
   - Monitors simulation frequency (max 10 per 10 min)
3. Simulation runs
4. **PostToolUse**: Sanitizes output

### Auto-Fix Loop (Protected!)
1. Issue detected in serial output
2. Triggers debug_and_fix
3. **Rate Anomaly Detection** (Layer 4):
   - Tracks API calls per minute
   - Tracks code modifications per round
   - Flags if > 5 fixes in rapid succession
4. Requires confirmation if anomaly detected
5. Prevents infinite fix loops

## Trust Progression

```
Trust Level 0/2 (Initial - Zero Trust)
├─ Code generation: ALLOWED (whitelisted)
├─ Safe read operations: ALLOWED
├─ Build commands: ALLOWED
├─ Dangerous ops: CONFIRM required

Trust Level 1/2 (After safe operations)
├─ All level 0 +
├─ More file modifications: ALLOWED
├─ Some API calls: ALLOWED

Trust Level 2/2 (Full trust)
├─ All operations allowed (except hard blacklist)
├─ Fast track: No CONFIRM needed
```

## Monitoring & Audit

### Real-Time Status
```bash
npx agent-guard status
# Shows:
# - Trust Level: 0/2
# - Safe Operations: 0
# - Last Deny: never
# - History Events: 0
```

### View Audit Log
```bash
npx agent-guard audit stats
npx agent-guard audit export
```

### Check Trust History
```bash
npx agent-guard trust history
npx agent-guard trust show
```

## Potential Issues & Solutions

### Issue 1: "BLOCKED: Multiple layers flagged"
**Cause**: Modification of sensitive files during zero-trust mode
**Solution**: Use trust escalation or whitelist the file
**Example**: Blocked writing to `.env` files - this is intentional

### Issue 2: "Rate limit exceeded: wokwi-cli"
**Cause**: Too many simulations in short time
**Solution**: Space out simulations or increase threshold
**Action**: Requires CONFIRM to proceed

### Issue 3: "Credentials detected in output"
**Cause**: API keys leaking in logs
**Solution**: Automatically sanitized by PostToolUse hook
**Visible**: Redacted in final output

## Commands Reference

### Check if operation is safe
```bash
npx agent-guard check --tool bash --args "rm -rf /"
# Response: 1 (DENY)

npx agent-guard check --tool write --args "sketch.ino"
# Response: 0 (ALLOW)
```

### Sanitize output
```bash
npx agent-guard sanitize --output "API_KEY=secret123"
# Redacts credentials from output
```

### Manage rules
```bash
npx agent-guard rules list          # List all rules
npx agent-guard rules test pattern  # Test rule pattern
npx agent-guard rules add <rule>    # Add new rule
npx agent-guard rules enable <name> # Enable disabled rule
```

### Trust management
```bash
npx agent-guard trust show          # Current trust level
npx agent-guard trust history       # Trust change history
npx agent-guard trust reset         # Reset to zero trust
```

### Configuration
```bash
npx agent-guard config show         # Show settings
npx agent-guard config set key val  # Change setting
```

## Performance Impact

- **PreToolUse latency**: < 5ms per check (P99: 1.087ms)
- **PostToolUse latency**: < 2ms per sanitization
- **Total overhead**: ~7ms per tool invocation
- **Memory footprint**: < 50MB

## Benefits for Arduino Tools

1. ✅ **Autonomous Operation**: Reduce need for user confirmation
2. ✅ **Safety Guardrails**: Prevent destructive operations
3. ✅ **Credential Protection**: Auto-redaction of API keys
4. ✅ **Loop Detection**: Prevent infinite fix cycles via rate limiting
5. ✅ **Audit Trail**: Complete record of all operations
6. ✅ **Gradual Trust**: Increase autonomy as system proves safe
7. ✅ **Invisible Integration**: Works silently in background

## Next Steps

### To Test Integration
1. Try generating a simple Arduino project
2. Monitor agent-guard logs: `npx agent-guard audit stats`
3. Observe trust level increase: `npx agent-guard trust show`
4. Trigger auto-fix and verify rate limiting

### To Customize Further
1. Edit `.agent-guard.yaml` to adjust rules
2. Add project-specific whitelist patterns
3. Adjust rate thresholds based on usage
4. Add custom credential redaction patterns

### To Monitor in Production
1. Set up audit log monitoring
2. Watch for DENY actions
3. Track trust level progression
4. Review sanitized outputs periodically

## Integration Status

| Component | Status | Details |
|-----------|--------|---------|
| Installation | ✅ | v0.1.0 installed globally |
| Claude Code Hooks | ✅ | PreToolUse & PostToolUse active |
| Project Initialization | ✅ | Risk map generated |
| Custom Rules | ✅ | .agent-guard.yaml configured |
| Auto-Detection | ✅ | Scanned 56 files, classified by risk |
| Trust System | ✅ | Zero trust mode active |
| Rate Limiting | ✅ | Anomaly detection enabled |
| Credential Protection | ✅ | Sanitization rules in place |

---

**Installation Date**: 2026-04-12
**Installed By**: Claude Code
**Project**: Arduino Tools (`E:\Arduino_tools\arduino_tools`)
**Configuration**: `.agent-guard.yaml` + global rules
