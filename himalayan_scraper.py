import requests

from datetime import datetime


def scrape_himalayan():
    jobs = []

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    url = "https://himalayas.app/jobs/api/search"
    params = {
        "page": 1,
        "country": "US",
        "sort": "recent",
        "pubDate": today,
        "seniority": "Mid-level",
    }

    for i in range(1):
        try:
            response = requests.get(url, params=params, timeout=10)
            print(response.url)
            if response.status_code == 200:
                jobs.extend(
                    [
                        job
                        for job in response.json()["jobs"]
                        if job["pubDate"] >= today.timestamp()
                    ]
                )
                print(datetime.fromtimestamp(response.json()["jobs"][-1]["pubDate"]))
                if response.json()["jobs"][-1]["pubDate"] < today.timestamp():
                    break
                else:
                    params["page"] += 1
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Scraping request failed: {e}")
            break

    return jobs


def himalayan_jobs_formatter():
    try:
        jobs = scrape_himalayan()
        jobs_with_salaries = [
            {
                "title": job["title"],
                "companyName": job["companyName"],
                "minSalary": job["minSalary"],
                "maxSalary": job["maxSalary"],
                "url": job["applicationLink"],
                "locationRestrictions": job["locationRestrictions"],
            }
            for job in jobs
            if job["title"]
            and job["companyName"]
            and job["minSalary"]
            and job["maxSalary"]
            and job["applicationLink"]
            and job["locationRestrictions"]
        ]
        companies = []
        new_jobs = []
        for job in jobs_with_salaries:
            if job["companyName"] not in companies and job["minSalary"] > 30000:
                companies.append(job["companyName"])
                new_jobs.append(job)
        return new_jobs
    except Exception as e:
        print(f"Error formatting Himalayan jobs: {e}")
        return []


data = himalayan_jobs_formatter()
print(len(data))
for i in data:
    print(i)