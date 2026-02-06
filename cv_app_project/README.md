# 🎯 AI CV Personalization Engine

Professional Streamlit application for AI-powered CV personalization using Resume Enhancer API.

## 📁 Project Structure

```
cv_app_project/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
│
├── config/                    # Configuration
│   ├── __init__.py
│   └── settings.py           # App configuration and constants
│
├── components/               # UI components
│   ├── __init__.py
│   ├── header.py            # Hero section
│   ├── upload_section.py    # Step 1: File upload & job description
│   ├── processing_section.py # Step 2: API processing
│   ├── results_section.py   # Step 3: Results display
│   ├── cv_comparison.py     # Side-by-side CV comparison
│   └── feedback_display.py  # Low match feedback
│
├── services/                # External services
│   ├── __init__.py
│   └── api_client.py       # Resume Enhancer API client
│
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── session_state.py    # Session state management
│   ├── validators.py       # Input validation
│   └── pdf_generator.py    # PDF generation
│
└── assets/                  # Static assets
    ├── __init__.py
    └── styles.py           # Custom CSS
```

## 🚀 Quick Start

### 1. Installation

```bash
cd cv_app_project
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Edit `config/settings.py` if needed:
- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- `MIN_MATCH_SCORE`: Threshold for high/low match (default: 6.0)
- `MAX_FILE_SIZE_MB`: Maximum upload size (default: 10MB)

### 3. Run Backend

Ensure your Resume Enhancer API is running:

```bash
uvicorn main:app --reload --port 8000
```

### 4. Run Frontend

```bash
streamlit run app.py
```

Open browser to: `http://localhost:8501`

## 🔌 API Integration

### Endpoints Used

#### 1. Parse Resume
```
POST /api/v1/parse
Content-Type: multipart/form-data

Body:
- file: CV file (.pdf or .docx)
- job_description: Job description text

Response: { resume: {...}, job_description: {...} }
```

#### 2. Enhance Resume
```
POST /api/v1/enhance
Content-Type: application/json

Body: { resume: {...}, job_description: {...} }

Response: { 
  mapping_result: {...}, 
  enhanced_resume: {...} (if score >= threshold),
  feedback_message: "..." (if score < threshold)
}
```

### Match Score Logic

- **Score ≥ 6.0**: High match → Side-by-side comparison
- **Score < 6.0**: Low match → Feedback with recommendations

## 📊 Features

### High Match (Score ≥ 60%)
- Side-by-side CV comparison
- Original CV on left
- Personalized CV on right
- Matched skills highlighted
- Skill gaps identified
- PDF download available

### Low Match (Score < 60%)
- Warning feedback card
- What you have (matched skills)
- What you're missing (gaps)
- Recommendations
- Analysis report download

## 🎨 Customization

### Change Match Threshold

Edit `config/settings.py`:
```python
MIN_MATCH_SCORE = 6.0  # Change to your preference (1-10 scale)
```

### Change API URL

Edit `config/settings.py`:
```python
API_BASE_URL = "https://your-api.com"
```

### Modify Colors

Edit `assets/styles.py`:
```python
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

## 🧪 Testing

### Test with Backend Running

```bash
streamlit run app.py
```

1. Upload a PDF or DOCX CV
2. Paste job description (min 50 characters)
3. Check consent box
4. Click "Generate Personalized CV"
5. View results

### API Health Check

```bash
curl http://localhost:8000/health
```

Expected: `{"status": "ok", "version": "..."}`

## 🐛 Troubleshooting

### "Failed to connect to backend"

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check API_BASE_URL in `config/settings.py`
3. Ensure no firewall blocking port 8000

### "PDF generation failed"

**Solution:**
```bash
pip install reportlab
```

### "File too large"

**Solution:**
- Compress your CV file
- Or increase MAX_FILE_SIZE_MB in `config/settings.py`

### "Request timed out"

**Solution:**
- Increase API_TIMEOUT in `config/settings.py`
- Check backend processing time
- Ensure backend has sufficient resources

## 📦 Dependencies

### Required
- `streamlit>=1.28.0` - Web framework
- `requests>=2.31.0` - HTTP client

### Optional
- `reportlab>=4.0.7` - PDF generation

## 🔒 Security Notes

- Never commit `.env` file
- Use environment variables for sensitive data
- Validate all user inputs
- Implement rate limiting on backend
- Use HTTPS in production

## 🚢 Deployment

### Streamlit Cloud

1. Push to GitHub
2. Go to share.streamlit.io
3. Deploy from repository
4. Add secrets in Streamlit settings

### Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

Build and run:
```bash
docker build -t cv-app .
docker run -p 8501:8501 cv-app
```

## 📝 API Response Examples

### High Match Response
```json
{
  "mapping_result": {
    "match_score": 8.5,
    "matched_skills": ["Python", "React", "AWS"],
    "gaps": ["Docker"],
    "matched_requirements": ["3+ years experience"]
  },
  "enhanced_resume": {
    "personal_info": {...},
    "summary": "...",
    "experiences": [...]
  },
  "change_report": [...]
}
```

### Low Match Response
```json
{
  "mapping_result": {
    "match_score": 3.5,
    "matched_skills": ["Python"],
    "gaps": ["ML", "TensorFlow", "Data Science"]
  },
  "feedback_message": "Consider targeting roles that better match..."
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

MIT License - feel free to use for your projects

## 📧 Support

For issues or questions:
- Check troubleshooting section
- Review API documentation
- Contact: support@example.com

---

**Built with ❤️ using Streamlit and Resume Enhancer API**
