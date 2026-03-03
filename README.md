# Daily Practicum & Internship Alerts (CA)

This Python script collects **open practicum and internship listings in California**, combining:  

1. **Local / on-site programs** (manually curated clinics & county programs)  
2. **Indeed RSS feeds** for counseling and mental health internships  
3. **LinkedIn alert emails**  
4. **Telehealth / remote positions** scraped from free Google search results  

The email output is split into **On-Site / Local** and **Telehealth / Remote** sections for easy scanning.

---

## Features

- ✅ Always shows local programs  
- ✅ Fetches relevant listings from Indeed RSS feeds  
- ✅ Parses LinkedIn alert emails  
- ✅ Pulls telehealth listings from Google search (free, no paid API)  
- ✅ Sends a **daily HTML email** with clickable links  
- ✅ Sections: **On-site** vs **Telehealth / Remote**  

---

## Prerequisites

- Python 3.x  
- Gmail account for sending/receiving emails  
- Environment variables:  

```bash
export EMAIL_ADDRESS="youremail@gmail.com"
export EMAIL_PASSWORD="your_app_password"