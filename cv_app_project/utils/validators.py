from config.settings import AppConfig

def format_file_size(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def validate_file(file) -> tuple[bool, str]:
    if file is None:
        return False, "No file uploaded"
    
    max_size = AppConfig.MAX_FILE_SIZE_MB * 1024 * 1024
    if file.size > max_size:
        return False, f"File too large (max {AppConfig.MAX_FILE_SIZE_MB}MB)"
    
    if file.type not in AppConfig.VALID_FILE_TYPES and \
       not file.name.lower().endswith(tuple(AppConfig.VALID_FILE_EXTENSIONS)):
        return False, "Invalid file type. Please upload PDF or DOCX"
    
    return True, "Valid file"

def validate_job_description(text: str) -> tuple[bool, str]:
    if not text or len(text.strip()) < AppConfig.MIN_JOB_DESC_LENGTH:
        return False, f"Job description too short (min {AppConfig.MIN_JOB_DESC_LENGTH} characters)"
    return True, "Valid"
