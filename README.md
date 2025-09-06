# AI-First Software Engineering (AFS) Maturity Assessment Framework

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-2.3%2B-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

The **AI-First Software Engineering (AFS) Maturity Assessment Framework** is a comprehensive self-evaluation tool that measures your team's maturity in adopting AI-driven software engineering practices. This assessment evaluates four critical dimensions of modern software development: Foundational Capabilities, Transformation Capabilities, Enterprise Integration, and Strategic Governance.

## Features

- **Comprehensive Assessment**: 23 detailed areas across 4 major dimensions
- **Maturity Scoring**: 4-level maturity classification (Traditional → AI-Assisted → AI-Augmented → AI-First)
- **Visual Reports**: Assessment results with detailed scoring breakdowns and recommendations
- **Streamlined Workflow**: Simplified assessment process and user interface
- **Assessor Tracking**: Capture assessor information for audit trails and accountability
- **Organization Context**: Detailed organization and team information collection
- **Database Migration**: Automated schema migration system for updates


## Assessment Framework

### Four Key Dimensions

1. **Foundational Capabilities (FC)** - 4 areas
   - AI Infrastructure & Tooling
   - Team AI Literacy & Skills
   - Code Generation & Review
   - Documentation & Knowledge Management

2. **Transformation Capabilities (TC)** - 5 areas
   - Intent-to-Architecture Translation
   - AI-Driven Testing & Quality Assurance
   - Continuous Integration & Deployment
   - Monitoring & Observability
   - Legacy System Modernization

3. **Enterprise Integration (EI)** - 6 areas
   - Data Governance & Management
   - Vendor & Tool Standardization
   - Integration with Enterprise Systems
   - Cost Management & ROI Tracking
   - Performance & Scalability Management
   - Business Continuity & Disaster Recovery

4. **Strategic Governance (SG)** - 8 areas
   - AI Ethics & Responsible AI
   - Performance Measurement & Value Realization
   - Intellectual Property Management
   - Risk Management & Security
   - Organizational Change Management
   - Cross-functional AI Collaboration
   - Regulatory Compliance
   - Innovation & Future Readiness

### Maturity Levels

- **Level 1 (Basic)**: Traditional/manual approaches
- **Level 2 (Evolving)**: Basic AI assistance
- **Level 3 (Advanced)**: Systematic AI integration
- **Level 4 (Optimized)**: Autonomous/AI-first approaches

## Assessment Methodology

The framework uses a comprehensive questionnaire-based approach where:

- **Structured Questions**: Each area contains specific questions designed to evaluate current practices
- **Evidence-Based Scoring**: Responses map to maturity levels based on observable practices and capabilities
- **Holistic Evaluation**: Assessment covers both technical implementation and organizational readiness
- **Benchmarking**: Results provide comparison against AI-first development best practices
- **Actionable Insights**: Detailed recommendations for progression to higher maturity levels
- **Progress Tracking**: Historical assessment data enables maturity evolution monitoring

## Technology Stack

- **Backend**: Python 3.8+, Flask 2.3+, SQLAlchemy
- **Database**: SQLite (default), with multi-adapter support
- **Frontend**: Jinja2 templates, Bootstrap 5, Custom JavaScript

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ai-first-software-engineering-maturity-assessment-framework.git
   cd ai-first-software-engineering-maturity-assessment-framework
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python scripts/setup_database.py
   ```

   This will:
   - Create the database schema (tables, indexes, views)
   - Populate with framework seed data (sections, areas, questions)
   - Verify the setup was successful

5. **Start the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://127.0.0.1:5000`

## Configuration

For custom configuration, copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

The default configuration uses SQLite and is ready to run without additional setup.

## Database Structure

The framework includes:
- **Core Framework Tables**: sections, areas, questions
- **Assessment Tables**: assessments (with organization and assessor fields), responses, assessment_sections  
- **Analytics Tables**: analytics_summary, question_analytics, team_progress
- **Support Tables**: assessment_recommendations, assessment_exports
- **Views**: Performance analytics and reporting views
- **Migration Tracking**: Schema versioning with automated migration system

## Core Workflow

The assessment framework provides a streamlined workflow:

1. **Home Page**: Overview and introduction to the AFS maturity assessment
2. **Organization Information**: Capture organization details and assessor information
3. **Section-by-Section Evaluation**: Complete assessments across four key dimensions:
   - Foundational Capabilities (FC) - 4 areas
   - Transformation Capabilities (TC) - 5 areas
   - Enterprise Integration (EI) - 6 areas
   - Strategic Governance (SG) - 8 areas
4. **Final Review**: Review all responses before submission
5. **Results**: View comprehensive maturity scores and recommendations

### Available URLs

- `/` - Home page with overview and statistics
- `/assessment/` - Assessment dashboard and listing
- `/assessment/create` - Create new assessment with organization and assessor information
- `/assessment/{id}/section/{section_id}` - Complete section assessments
- `/assessment/{id}/final-review` - Review before submission
- `/assessment/{id}/results` - View assessment results
- `/about` - About the framework and methodology


## Project Structure

```
├── app/                    # Main application package
│   ├── api/               # REST API endpoints
│   ├── blueprints/        # Flask blueprints for web routes
│   │   ├── main/          # Main pages (home, about)
│   │   └── assessment/    # Assessment workflow
│   ├── core/              # Core utilities (caching, logging)
│   ├── models/            # Database models and adapters
│   │   ├── assessment.py  # Enhanced with organization and assessor fields
│   │   └── database/      # Multi-database adapter support
│   ├── services/          # Business logic layer
│   │   ├── assessment_service.py  # Assessment management
│   │   ├── scoring_service.py     # Scoring calculations
│   │   └── recommendation_service.py # Recommendations
│   └── utils/             # Utility functions and helpers
├── config/                # Configuration files
├── data/                  # Database migrations and seed data
├── scripts/               # Management and deployment scripts
│   ├── setup_database.py  # Automated database setup
│   ├── database_schema.sql # Complete database schema (DDL)
│   └── database_seed_data.sql # Framework seed data (DML)
├── static/                # Static assets (CSS, JavaScript, images)
├── templates/             # Jinja2 templates
│   └── pages/assessment/  
│       ├── org_information.html # Organization and assessor info collection
│       └── ...            # Other assessment templates
├── instance/              # Instance-specific files (databases, configs)
├── logs/                  # Application logs  
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
└── .env.example           # Environment configuration template
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and development process.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/ai-first-software-engineering-maturity-assessment-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/ai-first-software-engineering-maturity-assessment-framework/discussions)

## Roadmap

- [ ] Enhanced assessment analytics
- [ ] Industry-specific assessment variations
- [ ] Integration with popular AI development tools
- [ ] Mobile-responsive improvements
- [ ] Multi-language support

---

*Transform your development practices. Measure your AFS maturity today.*