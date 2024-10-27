import os
import re
import shutil
from bs4 import BeautifulSoup

from report import load_report_config

def parse_filename(filename):
    pattern = r"^(?P<market>.*?)_(?P<lookback>\d+)_best_(?P<category>.*?)_report\.html$"
    match = re.match(pattern, filename)
    if match:
        market = match.group('market')
        lookback = match.group('lookback')
        category = match.group('category')
        return market, lookback, category
    else:
        return None

def merge_multiple_html_files(files_info, output_file):
    merged_soup = BeautifulSoup("<html><head><title>Merged Report</title></head><body></body></html>", 'html.parser')

    num_reports = len(files_info)
    style = merged_soup.new_tag('style')
    css_string = f"""
    .container {{
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
    }}
    .report {{
        width: calc(100% / {num_reports} - 20px);
        border: 1px solid #000;
        padding: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin: 10px;
        box-sizing: border-box;
        overflow: auto;
    }}
    h2 {{
        text-align: center;
    }}
    """
    style.string = css_string
    merged_soup.head.append(style)

    container_div = merged_soup.new_tag('div', **{'class': 'container'})

    for file_info in files_info:
        system_name = file_info['system_name']
        lookback = file_info['lookback']
        filepath = file_info['filepath']

        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        report_div = merged_soup.new_tag('div', **{'class': 'report'})

        heading = merged_soup.new_tag('h2')
        heading.string = f"{system_name} (Lookback: {lookback})"
        report_div.append(heading)

        if soup.body:
            report_content_html = soup.body.decode_contents()
        else:
            report_content_html = soup.decode_contents()
        report_content_soup = BeautifulSoup(report_content_html, 'html.parser')
        report_div.append(report_content_soup)

        container_div.append(report_div)

    merged_soup.body.append(container_div)

    with open(output_file, 'w', encoding='utf-8') as f_out:
        f_out.write(str(merged_soup.prettify()))

    print(f"Merged HTML file created at: {output_file}")


if __name__ == "__main__":
    import os
    import shutil

    cfg = load_report_config()
    systems = cfg.report.html_merger.systems
    output_directory = cfg.report.html_merger.output_dir

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    market_category_files = {}

    for system in systems:
        system_path = system
        html_files = [f for f in os.listdir(system_path) if f.endswith('.html')]
        for filename in html_files:
            parsed = parse_filename(filename)
            if parsed:
                market, lookback, category = parsed
                filepath = os.path.join(system_path, filename)
                if market not in market_category_files:
                    market_category_files[market] = {}
                if category not in market_category_files[market]:
                    market_category_files[market][category] = []
                market_category_files[market][category].append({
                    'system_name': system,
                    'lookback': lookback,
                    'filepath': filepath
                })

    for market, categories in market_category_files.items():
        for category, files_info in categories.items():
            if len(files_info) > 1:
                output_filename = f"{market}_merged_{category}_report.html"
                output_filepath = os.path.join(output_directory, output_filename)
                merge_multiple_html_files(files_info, output_filepath)
            else:
                file_info = files_info[0]
                source_filepath = file_info['filepath']
                output_filename = os.path.basename(source_filepath)
                output_filepath = os.path.join(output_directory, output_filename)
                shutil.copyfile(source_filepath, output_filepath)
                print(f"Copied HTML file to: {output_filepath}")
