# Bug Fixes and Features Documentation

## Version 1.2.0 - Content Extraction Control

### 🆕 New Feature: Content Extraction Switch

**Feature**: Added a master switch to enable/disable content extraction (FireCrawl + Zyte crawling).

**Configuration**:
```yaml
content_extraction:
  enabled: true   # Enable crawling (default)
  # or
  enabled: false  # Disable crawling, use RSS content only
```

**Benefits**:
- **Cost Control**: Disable expensive API calls when not needed
- **Speed Optimization**: Skip crawling for faster processing
- **Flexibility**: Choose between rich content vs. speed/cost
- **Backward Compatible**: Defaults to enabled if not specified

**Files Modified**:
- `config.yaml.template`: Added content_extraction.enabled setting
- `utils/news_processor.py`: Added switch logic in fetch_full_content_batch()
- `main.py`: Updated status display to show extraction settings
- `README.md`: Added configuration documentation

## Version 1.1.0 - Critical Bug Fixes

### 🐛 Fixed Issues

#### Issue #1: Empty Content in Feishu Push Messages
**Problem**: Feishu webhook received messages with empty titles and content, only containing links.

**Root Cause**: 
- AI optimization failures resulted in empty content being passed to webhook
- No content validation before pushing to Feishu
- Fallback mechanism didn't properly handle empty raw content

**Solution**:
- Added comprehensive content validation in `utils/news_processor.py`
- Implemented `_use_fallback_content()` method with multiple fallback sources
- Enhanced content verification to check both AI-optimized and original content
- Added debug logging for content validation failures

**Files Modified**:
- `utils/news_processor.py`: Enhanced content validation and fallback handling

#### Issue #2: Daemon Status Command Not Working
**Problem**: `python main.py daemon status` command failed to work properly on servers.

**Root Cause**:
- Relative path issues when starting background processes
- Insufficient error handling and logging for daemon operations
- Process group management issues

**Solution**:
- Fixed absolute path handling in daemon service startup
- Added proper process group creation with `preexec_fn=os.setsid`
- Enhanced error logging and status reporting
- Improved daemon startup verification with extended wait time
- Added startup and error log display for better debugging

**Files Modified**:
- `main.py`: Enhanced daemon service management and error handling

### 🔧 Technical Improvements

#### Content Validation Flow
```
AI Optimization Result
├── Success with content → Use optimized content
├── Success but empty → Use fallback content
├── Partial failure → Use available content or fallback
└── Complete failure → Use fallback content

Fallback Content Sources (in order):
1. Original raw_content
2. News description field
3. News summary field
4. Discard if all sources empty
```

#### Daemon Process Management
```
Daemon Startup Process:
1. Check existing PID file
2. Verify process is actually running
3. Create absolute script path
4. Start process with proper group isolation
5. Wait and verify startup success
6. Display startup logs for confirmation
```

### 🧪 Testing

Both fixes have been tested and verified:
- Content validation properly handles empty content scenarios
- Daemon commands work correctly with proper status reporting
- Background processes start and stop reliably
- Error logging provides clear debugging information

### 📋 Usage Examples

#### Content Validation
The system now properly validates content before pushing:
```bash
# If AI optimization fails, system will:
# 1. Try to use original content
# 2. Fall back to description if available
# 3. Discard news only if all content sources are empty
```

#### Daemon Management
All daemon commands now work reliably:
```bash
# Start daemon
python main.py start

# Check status with detailed logs
python main.py daemon status

# Stop daemon
python main.py stop

# Restart daemon
python main.py daemon restart
```

### 🚀 Deployment Notes

These fixes are backward compatible and don't require configuration changes. The improvements will automatically take effect after updating the code.

For server deployments:
1. Update the code
2. Restart any running daemon processes
3. Verify daemon status with `python main.py daemon status`

### 📊 Impact

- **Reliability**: Eliminates empty content pushes to Feishu
- **Usability**: Daemon commands work consistently across environments
- **Debugging**: Enhanced logging for better troubleshooting
- **Robustness**: Better error handling and recovery mechanisms
