# Citation Mind - Usage Guide

## Quick Start Guide

### 1. Installation

```bash
cd citation-mind
pip install -r requirements.txt
pip install -e .
```

### 2. Initialize Your Profile

```bash
citation-mind init
```

You'll be prompted for:
- Your ORCID ID (format: 0000-0000-0000-0000)
- Your email address
- Your full name

### 3. Configure API Keys (Optional but Recommended)

Create a `.env` file in `~/.citation-mind/`:

```bash
# Semantic Scholar (recommended - free)
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# ORCID (optional - for private data)
ORCID_CLIENT_ID=your_client_id
ORCID_CLIENT_SECRET=your_client_secret

# Web of Science (requires institutional access)
WOS_API_KEY=your_wos_key

# Scopus (requires institutional access)
SCOPUS_API_KEY=your_scopus_key
```

**Getting API Keys:**

- **Semantic Scholar**: Free at https://www.semanticscholar.org/product/api
- **ORCID**: Register at https://orcid.org/developer-tools
- **Web of Science / Scopus**: Check with your institution's library

### 4. Fetch Your Citation Data

```bash
# Fetch from all enabled platforms
citation-mind fetch --all

# Or fetch from specific platforms
citation-mind fetch --platform semantic_scholar
citation-mind fetch --platform orcid --platform arxiv
```

### 5. View Your Dashboard

```bash
# Quick overview
citation-mind dashboard

# Detailed view with top papers
citation-mind dashboard --detailed

# Specific time period
citation-mind dashboard --period month
```

## Core Features

### Citation Tracking

Track your citations across multiple platforms:

```bash
# Track all papers
citation-mind fetch --all

# Track specific paper
citation-mind track --doi "10.1234/example"
citation-mind track --arxiv "2301.12345"

# List tracked papers
citation-mind track --list
```

### Get Recommendations

The tool analyzes your citation profile and provides actionable recommendations:

```bash
# Get top 5 recommendations
citation-mind recommend

# Get more recommendations
citation-mind recommend --top 10

# Filter by category
citation-mind recommend --category visibility
citation-mind recommend --category collaboration
citation-mind recommend --category trending
```

**Recommendation Categories:**

1. **Visibility**: Promote under-cited papers, add DOIs, improve discoverability
2. **Collaboration**: Increase co-authorship, network with researchers
3. **Trending**: Align research with current hot topics
4. **Profile**: Complete profiles, activate more platforms

### View Statistics

```bash
# Overall statistics
citation-mind stats

# Specific paper statistics
citation-mind stats --paper "10.1234/example"
```

### Export Data

```bash
# Export to CSV (default)
citation-mind export

# Export to JSON
citation-mind export --format json --output my_citations.json

# Export to Excel
citation-mind export --format xlsx --output citations.xlsx
```

### Set Up Alerts

```bash
# Enable citation alerts
citation-mind alert --enable

# Set threshold (alert when paper gets N+ citations)
citation-mind alert --threshold 5

# Disable alerts
citation-mind alert --disable
```

## Platform-Specific Notes

### ORCID
- **Free**, no API key needed for public data
- Most reliable for publication lists
- Doesn't provide citation counts directly
- Good starting point for building your paper database

### arXiv
- **Free**, no API key needed
- Great for preprints and open access papers
- Doesn't provide citation counts
- Use in combination with Semantic Scholar for citations

### Semantic Scholar
- **Free** API available (recommended!)
- Provides citation counts
- Good coverage of computer science, biomedical papers
- Fast and reliable
- **Best platform for citation tracking**

### Google Scholar
- No official API
- Tool uses `scholarly` library (may be rate-limited)
- Most comprehensive coverage
- Can be blocked by Google
- Use sparingly

### Web of Science & Scopus
- Require institutional access
- Subscription-based
- High-quality citation data
- Best for established researchers with institution access

## Best Practices for Increasing Citations

Based on the recommendations engine, here are proven strategies:

### 1. **Profile Optimization**
- Complete all profiles (ORCID, Google Scholar, ResearchGate, etc.)
- Keep profiles updated with latest publications
- Add keywords and research interests
- Use consistent name across platforms

### 2. **Paper Visibility**
- Always get a DOI for your papers
- Upload preprints to arXiv/bioRxiv
- Share on social media (Twitter/X, LinkedIn)
- Add papers to institutional repositories
- Submit to open access journals when possible

### 3. **Strategic Promotion**
- Share on ResearchGate and Academia.edu
- Present at conferences
- Write blog posts explaining your research
- Contact researchers citing similar work
- Participate in relevant online communities

### 4. **Collaboration**
- Co-author with established researchers
- Join research groups and consortiums
- Participate in multi-institution studies
- Attend workshops and networking events

### 5. **Content Quality**
- Write clear, accessible abstracts
- Use descriptive titles with keywords
- Include good figures and visualizations
- Provide code and data when possible
- Write reproducible research

### 6. **Timing & Trends**
- Publish in active research areas
- Reference recent high-impact papers
- Follow trending topics in your field
- Consider interdisciplinary work

## Automation

### Scheduled Updates

Set up a cron job to fetch data weekly:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Sunday at 2 AM)
0 2 * * 0 /usr/bin/citation-mind fetch --all
```

### Email Alerts (Future Feature)

Configure email notifications in `~/.citation-mind/config.yaml`:

```yaml
alerts:
  enabled: true
  email_notifications: true
  min_citation_threshold: 1
```

## Troubleshooting

### "Not initialized" Error
Run `citation-mind init` first.

### No Data Fetched
- Check your internet connection
- Verify your ORCID ID is correct
- Ensure API keys are properly set (if using)
- Some platforms may be rate-limiting

### Google Scholar Blocked
Google Scholar often blocks automated requests. Solutions:
- Use less frequently
- Disable Google Scholar platform
- Use Semantic Scholar instead (better API)

### Missing Citations
- Different platforms have different coverage
- Some papers take time to appear in databases
- Ensure papers have DOIs
- Check that author names match across platforms

## Advanced Usage

### Custom Database Location

Edit `~/.citation-mind/config.yaml`:

```yaml
database:
  path: "/custom/path/citations.db"
```

### Disable Specific Platforms

```yaml
platforms:
  google_scholar:
    enabled: false
```

### Adjust Fetch Intervals

```yaml
tracking:
  auto_fetch: true
  fetch_interval_hours: 48  # Fetch every 2 days
```

## Contributing

Found a bug or want to add a feature? The project structure is:

```
citation-mind/
├── src/
│   ├── api/           # Platform integrations
│   ├── core/          # CLI and configuration
│   ├── db/            # Database management
│   └── analytics/     # Metrics and recommendations
├── config/            # Configuration templates
└── data/              # Local data storage
```

## Support

For issues and feature requests, check the project documentation or open an issue on GitHub.

---

**Remember**: Increasing citations is a long-term process. Use this tool to track progress, identify opportunities, and stay informed about your research impact!
