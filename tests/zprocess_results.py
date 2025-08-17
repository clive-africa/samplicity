import pandas as pd
import json

def process_test_results(df):
    """Process test results and generate summary statistics."""
    # Calculate overall statistics
    total_tests = len(df)
    passed_tests = df['pass'].sum()
    overall_pass_rate = round((passed_tests / total_tests) * 100, 2)
    
    # Group by class/module
    module_results = []
    grouped = df.groupby('class').agg({
        'pass': ['sum', 'count']
    }).reset_index()
    
    for _, row in grouped.iterrows():
        module_results.append({
            'class': row['class'],
            'passed': int(row[('pass', 'sum')]),
            'total': int(row[('pass', 'count')]),
            'pass_rate': round((row[('pass', 'sum')] / row[('pass', 'count')]) * 100, 2)
        })
    
    # Get failed test details
    failed_tests = []
    for _, row in df[~df['pass']].iterrows():
        failed_tests.append({
            'class': row['class'],
            'category': row['category'],
            'expected': float(row['test_result']),
            'actual': float(row['python_result'])
        })
    
    # Create summary
    summary = {
        'overall_pass_rate': overall_pass_rate,
        'total_tests': total_tests,
        'passed_tests': int(passed_tests),
        'module_results': module_results,
        'failed_tests': failed_tests
    }
    
    # Save to file
    with open('test_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    # Read the test results from your test execution
    results_df = pd.read_csv('test_results.csv')  # Adjust path as needed
    process_test_results(results_df)