from application_link_spider import ApplicationLinkSpider
from himalayan_scraper import himalayan_jobs_formatter


def main():
    jobs = himalayan_jobs_formatter()
    print(f"Found {len(jobs)} jobs to process\n")

    with ApplicationLinkSpider(headless=False) as spider:
        results = spider.process_jobs(jobs)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    no_button = [r for r in results if r['status'] == 'no_apply_button']

    print(f"Total jobs processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"No apply button found: {len(no_button)}")
    print(f"Failed: {len(failed)}")

    print("\n" + "="*80)
    print("FINAL URLS")
    print("="*80)
    for result in results:
        if result['final_url']:
            print(f"{result['company']} - {result['job_title']}")
            print(f"  Original: {result['original_url']}")
            print(f"  Final: {result['final_url']}")
            print()

    return results


if __name__ == "__main__":
    main()