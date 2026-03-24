from application_link_spider import ApplicationLinkSpider
from himalayan_scraper import himalayan_jobs_formatter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def create_pdf(results, filename="job_results.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    for result in results:
        if result['final_url']:
            link_text = f"{result['job_title']} ({result['company']}) - {result['minSalary']}-{result['maxSalary']} USD"
            link_html = f'<link href="{result["final_url"]}" color="blue">{link_text}</link>'
            paragraph = Paragraph(link_html, styles['Normal'])
            story.append(paragraph)
            story.append(Spacer(1, 0.2*inch))

    doc.build(story)
    print(f"PDF created: {filename}")


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

    # Create PDF instead of printing
    create_pdf(results)

    return results


if __name__ == "__main__":
    main()