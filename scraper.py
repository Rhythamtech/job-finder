import requests
from dotenv import load_dotenv
import random
import json
import os
import re

load_dotenv()


class NaurkiScraper:
    def __init__(self):
        self.url = "https://www.naukri.com/jobapi/v3/search"
        self.system_id = random.randint(100, 999)
        self.app_id = random.randint(100, 999)
        # random 4 character string include alpha numeric character
        self.client_id = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
        self.headers = {
            "accept": "application/json",
            "appid": str(self.app_id),
            "clientid": str(self.client_id),
            "content-type": "application/json",
            "expires": "0",
            "nkparam": os.getenv("NAUKRI_NKPARAM"),
            "priority": "u=1, i",
            "systemid": str(self.system_id),
            "user-agent": "Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
        }

    def parsed_naukri_data(self, data):
            jobs_data = []

            # 2. Iterate through the job list
            if 'jobDetails' in data:
                for job in data['jobDetails']:
                    # -- Core Identity --
                    job_id = job.get('jobId')
                    title = job.get('title')
                    company = job.get('companyName')
                    
                    # -- Logo Extraction (Added) --
                    logo_path = job.get('logoPath')
                    
                    # -- Safe Rating Extraction --
                    rating = None
                    if 'ambitionBoxData' in job and job['ambitionBoxData']:
                        rating = job['ambitionBoxData'].get('AggregateRating')
                    
                    # -- Placeholder Parsing (Location & Salary) --
                    location = "Not specified"
                    salary = "Not disclosed"
                    experience = job.get('experienceText', "Not specified")

                    placeholders = job.get('placeholders', [])
                    for p in placeholders:
                        if p.get('type') == 'location':
                            location = p.get('label')
                        elif p.get('type') == 'salary':
                            salary = p.get('label')
                        elif p.get('type') == 'experience' and experience == "Not specified":
                            experience = p.get('label')

                    # -- Dates --
                    post_date = job.get('createdDate')
                    
                    # -- Skills Aggregation --
                    skills = []
                    key_skills = job.get('keySkills', {})
                    if key_skills:
                        # Combine 'otherSkills', 'mandatorySkills', 'nerSkills'
                        for skill_type, skill_list in key_skills.items():
                            if isinstance(skill_list, list) and skill_type != 'tagsOrder':
                                skills.extend(skill_list)
                        skills = list(set(skills)) # Remove duplicates

                    # -- URL Correction --
                    url = job.get('jdURL')
                    if url and not url.startswith('http'):
                        url = "https://www.naukri.com" + url
                    
                    # -- Append to List --
                    jobs_data.append({
                        'job_id': job_id,
                        'title': title,
                        'company': company,
                        'logo_path': logo_path,  # Added here
                        'rating': rating,
                        'location': location,
                        'salary': salary,
                        'experience': experience,
                        'post_date': post_date,
                        'skills': ", ".join(skills), 
                        'url': url,
                        'description': job.get('jobDescription')  # Added JD extraction
                    })

            return jobs_data

    def scrape(self, location, search_term, job_type, experience, page_count):
        job_type_dict = {
            "Work from office" : "0",
            "Remote" : "2",
            "Hybrid" : "3"
        }

        jobs = []

        params = {
            "location": location,
            "keyword": search_term,
            "k": search_term,
            "searchType": "adv_1",
            "urlType": "search_by_key_loc",
            "experience": str(experience),
            "pageNo": "1",
            "src":"pagination-searchFormUsage",
            "jobAge":"1",
            "sort" : "f",
            "noOfResults": "20"
        }

        for i in range(0, page_count):
            params["pageNo"] = str(i+1)
            
            try:
                response = requests.get(self.url, headers=self.headers, params=params)
                print(f"Status Code: {response.status_code}")
            
                if response.status_code == 200:
                    data = response.json()
                    jobs_data = self.parsed_naukri_data(data)
                    jobs.extend(jobs_data)

                else:
                    print(f"Error: {response.text}")
            except Exception as e:
                print(f"Exception: {str(e)}")

        return jobs
    
HIRIST_LOCATIONS = {
    "Metros": 87,
    "Anywhere in India": 88,
    "Overseas": 89,
    "International": 89,
    "Ahmedabad": 53,
    "Amritsar": 45,
    "Andhra Pradesh": 34,
    "Aurangabad": 79,
    "Bangalore": 3,
    "Bhubaneshwar": 65,
    "Bihar": 19,
    "Chandigarh": 14,
    "Chennai": 6,
    "Chhattisgarh": 64,
    "Cochin": 70,
    "Kochi": 70,
    "Coimbatore": 84,
    "Cuttack": 86,
    "Dehradun": 58,
    "Delhi": 36,
    "Delhi NCR": 1,
    "Faridabad": 40,
    "Gandhinagar": 55,
    "Ghaziabad": 41,
    "Goa": 13,
    "Greater Noida": 39,
    "Gujarat": 8,
    "Guntur": 77,
    "Gurgaon": 37,
    "Gurugram": 37,
    "Guwahati": 12,
    "Haridwar": 57,
    "Haryana": 16,
    "Hosur": 71,
    "Hubli": 72,
    "Hyderabad": 4,
    "Jaipur": 11,
    "Jalandhar": 46,
    "Jammu": 43,
    "Jammu & Kashmir": 42,
    "Jamshedpur": 63,
    "Jharkhand": 20,
    "Jodhpur": 52,
    "Karnataka": 31,
    "Kerala": 17,
    "Kolkata": 5,
    "Lucknow": 60,
    "Ludhiana": 48,
    "Madurai": 83,
    "Maharashtra": 9,
    "MP": 10,
    "Mumbai": 2,
    "Mysore": 73,
    "Nagpur": 66,
    "Nasik": 67,
    "Navi Mumbai": 68,
    "Noida": 38,
    "Odisha": 18,
    "Panipat": 50,
    "Patiala": 47,
    "Patna": 61,
    "Pondicherry": 85,
    "Pune": 7,
    "Punjab": 15,
    "Raipur": 74,
    "Rajasthan": 33,
    "Rajkot": 80,
    "Ranchi": 62,
    "Sonipat": 49,
    "Srinagar": 44,
    "Surat": 54,
    "Tamil Nadu": 32,
    "Telangana": 35,
    "Thane": 69,
    "Trivandrum": 75,
    "Thiruvananthapuram": 75,
    "Udaipur": 51,
    "UP": 21,
    "Uttarakhand": 59,
    "Vadodara": 56,
    "Baroda": 56,
    "Varanasi": 81,
    "Banaras": 81,
    "Vijayawada": 76,
    "Vishakhapatnam": 78,
    "Vizag": 78,
    "Warangal": 82,
    "Abu Dhabi": 100,
    "Afghanistan": 109,
    "Africa": 26,
    "Bahrain": 90,
    "Bangladesh": 107,
    "Bhutan": 105,
    "China": 108,
    "Dhaka": 106,
    "Doha": 98,
    "Dubai": 91,
    "Egypt": 113,
    "Ethiopia": 112,
    "EU": 28,
    "Hong Kong": 30,
    "Indonesia": 103,
    "Kabul": 92,
    "Kenya": 114,
    "Kuwait": 93,
    "London": 95,
    "Malaysia": 27,
    "Middle East": 25,
    "Muscat": 97,
    "Nairobi": 115,
    "Nepal": 104,
    "Nigeria": 94,
    "Oman": 96,
    "Pakistan": 110,
    "Philippines": 120,
    "Qatar": 99,
    "Riyadh": 102,
    "Saudi Arabia": 101,
    "Singapore": 24,
    "South Africa": 117,
    "Sri Lanka": 111,
    "Tanzania": 116,
    "UK": 23,
    "US": 22,
    "Zambia": 119,
    "Zimbabwe": 118,
    "Others": 100000,
    "Mizoram": 122,
    "Assam": 123,
    "Manipur": 124,
    "Meghalaya": 125,
    "Tripura": 126,
    "Arunachal Pradesh": 127,
    "Nagaland": 128,
    "West Bengal": 129,
    "Indore": 130,
    "Bhopal": 121,
    "Mohali": 131,
    "Remote": 132
}

class HiristScraper:
    def __init__(self):
        self.url = "https://gladiator.hirist.tech/job/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Cookie': 'PHPSESSID=d399d6dd2ad14236a689c70e577030ee'
        }

    def parsed_hirist_data(self, data):
        jobs_data = []
        if 'data' in data:
            for job in data['data']:
                job_id = str(job.get('id'))
                title = job.get('title')
                
                company_data = job.get('companyData', {})
                company = company_data.get('companyName')
                logo_path = company_data.get('logo')
                
                rating = str(job.get('minRatingAb', ''))
                if not rating and 'ambitionBoxInfo' in company_data:
                    rating = str(company_data['ambitionBoxInfo'].get('aggregateRating', ''))

                # Locations
                locs = [l.get('name') for l in job.get('locations', []) if l.get('name')]
                location = ", ".join(locs) if locs else "Not specified"

                # Salary
                min_sal = job.get('minSal')
                max_sal = job.get('maxSal')
                salary = "Not disclosed"
                if min_sal is not None and max_sal is not None:
                    salary = f"{min_sal}-{max_sal} LPA"

                # Experience
                min_exp = job.get('min')
                max_exp = job.get('max')
                experience = f"{min_exp}-{max_exp} Yrs" if min_exp is not None else "Not specified"

                post_date = job.get('createdTimeMs')
                
                # Skills
                tags = [t.get('name') for t in job.get('tags', []) if t.get('name')]
                skills = ", ".join(tags) if tags else "Not specified"

                url = job.get('jobDetailUrl')

                # Generate description template as requested by user
                description = f"{company} is actively seeking a qualified {title} to join our growing team. The ideal candidate requires {experience} of relevant industry experience. We are offering a competitive compensation package of {salary}. The primary technical requirements for this role include: {skills}."

                jobs_data.append({
                    'job_id': job_id,
                    'title': title,
                    'company': company,
                    'logo_path': logo_path,
                    'rating': rating,
                    'location': location,
                    'salary': salary,
                    'experience': experience,
                    'post_date': post_date,
                    'skills': skills,
                    'url': url,
                    'description': description
                })
        return jobs_data

    def get_location_id(self, location_name):
        if not location_name:
            return 88 
        
        if location_name in HIRIST_LOCATIONS:
            return HIRIST_LOCATIONS[location_name]
            
        loc_lower = location_name.lower()
        for k, v in HIRIST_LOCATIONS.items():
            if k.lower() == loc_lower:
                return v
        
        for k, v in HIRIST_LOCATIONS.items():
            if k.lower() in loc_lower or loc_lower in k.lower():
                return v
                
        return 132 

    def scrape(self, query, location, min_exp=2, max_exp=3, page_count=1, size=20):
        loc_names = []
        if location:
            loc_names = [l.strip() for l in location.split(',') if l.strip()]
        
        if not loc_names:
            loc_names = [""]

        loc_ids = set()
        for name in loc_names:
            loc_ids.add(self.get_location_id(name))

        loc_param = ",".join(map(str, loc_ids))
        all_jobs = []
        
        for page in range(page_count):
            params = {
                'minexp': min_exp,
                'maxexp': max_exp,
                'query': query,
                'page': page,
                'loc': loc_param,
                'posting': 0,
                'size': size
            }

            try:
                response = requests.get(self.url, headers=self.headers, params=params)
                print(f"Status Code: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    jobs = self.parsed_hirist_data(data)
                    all_jobs.extend(jobs)
                else:
                    print(f"Error: {response.text}")
            except Exception as e:
                print(f"Exception: {str(e)}")
                
        return all_jobs

if __name__ == "__main__":

    scraper = NaurkiScraper()
    jobs = scraper.scrape(search_term="Python Developer", location="Bangalore,Gurugram, Noida",job_type="Full Time",experience=2, page_count=2)
    with open("scraped_data.json", "w") as f:
        json.dump(jobs, f, indent=4)    


    # hirist_scraper = HiristScraper()
    # jobs = hirist_scraper.scrape(query="Python Developer", location="Bangalore,Gurugram, Noida",min_exp=2, max_exp=3, page_count=2)
    # with open("scraped_data.json", "w") as f:
    #     json.dump(jobs, f, indent=4)        