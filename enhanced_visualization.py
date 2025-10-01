# enhanced_visualization.py
# Generate publication-quality visualizations for assignment report

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from data_access.database_manager import DatabaseManager
from utilities.logger import get_logger


class ReportVisualizationGenerator:
    """
    Generate high-quality visualizations for assignment report.
    Creates professional charts suitable for academic submission.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
        self.output_dir = 'outputs/charts'
        os.makedirs(self.output_dir, exist_ok=True)

        # Set professional style
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 9

    def generate_all_report_charts(self):
        """Generate all charts needed for the report"""
        print("\n" + "=" * 70)
        print("GENERATING VISUALIZATIONS FOR REPORT")
        print("=" * 70)

        charts_created = []

        # Chart 1: Route Comparison Bar Chart
        print("\n1. Creating route comparison chart...")
        chart1 = self.create_route_comparison_chart()
        charts_created.append(chart1)

        # Chart 2: Hourly Traffic Pattern
        print("2. Creating hourly traffic pattern...")
        chart2 = self.create_hourly_pattern_chart()
        charts_created.append(chart2)

        # Chart 3: Weather Impact
        print("3. Creating weather impact visualization...")
        chart3 = self.create_weather_impact_chart()
        charts_created.append(chart3)

        # Chart 4: Peak vs Off-Peak Comparison
        print("4. Creating peak vs off-peak comparison...")
        chart4 = self.create_peak_offpeak_comparison()
        charts_created.append(chart4)

        # Chart 5: Day Type Comparison
        print("5. Creating day type comparison...")
        chart5 = self.create_day_type_comparison()
        charts_created.append(chart5)

        # Chart 6: Traffic Heatmap
        print("6. Creating traffic heatmap...")
        chart6 = self.create_traffic_heatmap()
        charts_created.append(chart6)

        # Chart 7: Distribution Analysis
        print("7. Creating distribution analysis...")
        chart7 = self.create_distribution_analysis()
        charts_created.append(chart7)

        # Chart 8: Time Series Trend
        print("8. Creating time series trend...")
        chart8 = self.create_time_series_trend()
        charts_created.append(chart8)

        print("\n" + "=" * 70)
        print(f"✅ Created {len(charts_created)} visualizations")
        print(f"📁 Saved to: {self.output_dir}/")
        print("=" * 70)

        for chart in charts_created:
            print(f"  • {os.path.basename(chart)}")

        return charts_created

    def create_route_comparison_chart(self) -> str:
        """Bar chart comparing average times across routes"""
        routes = self.db_manager.get_all_routes()

        route_data = []
        for route in routes[:10]:  # Top 10 routes
            analytics = self.db_manager.get_route_analytics(route.name)
            if analytics and analytics.total_records > 0:
                route_data.append({
                    'Route': route.name[:25],  # Truncate long names
                    'Avg Time': analytics.average_travel_time,
                    'Peak': analytics.peak_hour_average,
                    'Off-Peak': analytics.off_peak_average
                })

        df = pd.DataFrame(route_data)
        df = df.sort_values('Avg Time')

        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(df))
        width = 0.25

        ax.bar(x - width, df['Avg Time'], width, label='Average', color='#3498db')
        ax.bar(x, df['Peak'], width, label='Peak Hours', color='#e74c3c')
        ax.bar(x + width, df['Off-Peak'], width, label='Off-Peak', color='#2ecc71')

        ax.set_xlabel('Route', fontweight='bold')
        ax.set_ylabel('Travel Time (minutes)', fontweight='bold')
        ax.set_title('Route Comparison: Average Travel Times', fontweight='bold', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(df['Route'], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        filepath = f"{self.output_dir}/1_route_comparison.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath

    def create_hourly_pattern_chart(self) -> str:
        """Line chart showing traffic patterns by hour"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=30)

        hourly_stats = df.groupby('hour')['travel_time_minutes'].agg(['mean', 'std', 'count'])

        fig, ax = plt.subplots(figsize=(12, 6))

        hours = hourly_stats.index
        means = hourly_stats['mean']
        stds = hourly_stats['std']

        ax.plot(hours, means, marker='o', linewidth=2, markersize=6, color='#3498db', label='Average Time')
        ax.fill_between(hours, means - stds, means + stds, alpha=0.2, color='#3498db', label='±1 Std Dev')

        # Highlight peak hours
        peak_hours = [7, 8, 9, 17, 18, 19]
        for hour in peak_hours:
            if hour in hours:
                ax.axvspan(hour - 0.5, hour + 0.5, alpha=0.1, color='red')

        ax.set_xlabel('Hour of Day', fontweight='bold')
        ax.set_ylabel('Travel Time (minutes)', fontweight='bold')
        ax.set_title('24-Hour Traffic Pattern Analysis', fontweight='bold', fontsize=14)
        ax.set_xticks(range(0, 24, 2))
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add annotations
        ax.text(8, ax.get_ylim()[1] * 0.95, 'Morning Rush', ha='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.text(18, ax.get_ylim()[1] * 0.95, 'Evening Rush', ha='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        filepath = f"{self.output_dir}/2_hourly_pattern.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath

    def create_weather_impact_chart(self) -> str:
        """Bar chart showing weather impact on travel times"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=60)

        weather_stats = df.groupby('weather_condition')['travel_time_minutes'].agg(['mean', 'std', 'count'])
        weather_stats = weather_stats.sort_values('mean')

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
        bars = ax.barh(weather_stats.index, weather_stats['mean'],
                       xerr=weather_stats['std'], capsize=5, color=colors)

        ax.set_xlabel('Average Travel Time (minutes)', fontweight='bold')
        ax.set_ylabel('Weather Condition', fontweight='bold')
        ax.set_title('Impact of Weather Conditions on Travel Time', fontweight='bold', fontsize=14)
        ax.grid(axis='x', alpha=0.3)

        # Add value labels
        for i, (idx, row) in enumerate(weather_stats.iterrows()):
            ax.text(row['mean'] + 1, i, f"{row['mean']:.1f} min\n(n={int(row['count'])})",
                    va='center', fontsize=9)

        plt.tight_layout()
        filepath = f"{self.output_dir}/3_weather_impact.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath

    def create_peak_offpeak_comparison(self) -> str:
        """Box plot comparing peak vs off-peak traffic"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=30)

        df['Period'] = df['hour'].apply(lambda x: 'Peak Hours' if x in [7, 8, 9, 17, 18, 19] else 'Off-Peak')

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.boxplot(data=df, x='Period', y='travel_time_minutes', ax=ax,
                    palette={'Peak Hours': '#e74c3c', 'Off-Peak': '#2ecc71'})
        sns.swarmplot(data=df.sample(min(200, len(df))), x='Period', y='travel_time_minutes',
                      ax=ax, color='black', alpha=0.3, size=2)

        ax.set_xlabel('Time Period', fontweight='bold')
        ax.set_ylabel('Travel Time (minutes)', fontweight='bold')
        ax.set_title('Peak vs Off-Peak Traffic Comparison', fontweight='bold', fontsize=14)
        ax.grid(axis='y', alpha=0.3)

        # Add statistical annotation
        peak_median = df[df['Period'] == 'Peak Hours']['travel_time_minutes'].median()
        offpeak_median = df[df['Period'] == 'Off-Peak']['travel_time_minutes'].median()
        diff = peak_median - offpeak_median

        ax.text(0.5, ax.get_ylim()[1] * 0.95,
                f'Median Difference: {diff:.1f} minutes ({diff / offpeak_median * 100:.1f}% increase)',
                ha='center', transform=ax.transData,
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

        plt.tight_layout()
        filepath = f"{self.output_dir}/4_peak_offpeak_comparison.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath

    def create_day_type_comparison(self) -> str:
        """Violin plot comparing different day types"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=60)

        fig, ax = plt.subplots(figsize=(10, 6))

        sns.violinplot(data=df, x='day_type', y='travel_time_minutes', ax=ax,
                       palette='Set2', inner='quartile')

        ax.set_xlabel('Day Type', fontweight='bold')
        ax.set_ylabel('Travel Time (minutes)', fontweight='bold')
        ax.set_title('Travel Time Distribution by Day Type', fontweight='bold', fontsize=14)
        ax.grid(axis='y', alpha=0.3)

        # Add mean values
        day_means = df.groupby('day_type')['travel_time_minutes'].mean()
        for i, (day, mean) in enumerate(day_means.items()):
            ax.text(i, mean, f'μ={mean:.1f}', ha='center', va='bottom',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        plt.tight_layout()
        filepath = f"{self.output_dir}/5_day_type_comparison.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath

    def create_traffic_heatmap(self) -> str:
        """Heatmap showing traffic intensity by hour and day"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=30)

        pivot_table = df.pivot_table(values='travel_time_minutes',
                                     index='hour',
                                     columns='day_of_week',
                                     aggfunc='mean')

        fig, ax = plt.subplots(figsize=(12, 8))

        sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
                    cbar_kws={'label': 'Average Travel Time (minutes)'}, linewidths=0.5)

        ax.set_xlabel('Day of Week (0=Monday, 6=Sunday)', fontweight='bold')
        ax.set_ylabel('Hour of Day', fontweight='bold')
        ax.set_title('Traffic Intensity Heatmap', fontweight='bold', fontsize=14)

        plt.tight_layout()
        filepath = f"{self.output_dir}/6_traffic_heatmap.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath

    def create_distribution_analysis(self) -> str:
        """Histogram with distribution analysis"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=60)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Travel Time Distribution Analysis', fontweight='bold', fontsize=16)

        # Overall distribution
        ax1 = axes[0, 0]
        ax1.hist(df['travel_time_minutes'], bins=30, edgecolor='black', alpha=0.7, color='#3498db')
        ax1.axvline(df['travel_time_minutes'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
        ax1.axvline(df['travel_time_minutes'].median(), color='green', linestyle='--', linewidth=2, label='Median')
        ax1.set_xlabel('Travel Time (minutes)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Overall Distribution')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # By hour
        ax2 = axes[0, 1]
        peak_data = df[df['hour'].isin([7, 8, 9, 17, 18, 19])]['travel_time_minutes']
        offpeak_data = df[~df['hour'].isin([7, 8, 9, 17, 18, 19])]['travel_time_minutes']
        ax2.hist([peak_data, offpeak_data], bins=20, label=['Peak', 'Off-Peak'],
                 alpha=0.7, color=['#e74c3c', '#2ecc71'])
        ax2.set_xlabel('Travel Time (minutes)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Peak vs Off-Peak Distribution')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

        # By weather
        ax3 = axes[1, 0]
        for weather in df['weather_condition'].unique():
            weather_data = df[df['weather_condition'] == weather]['travel_time_minutes']
            ax3.hist(weather_data, bins=15, alpha=0.5, label=weather)
        ax3.set_xlabel('Travel Time (minutes)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Distribution by Weather')
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)

        # Q-Q Plot
        ax4 = axes[1, 1]
        from scipy import stats
        stats.probplot(df['travel_time_minutes'].dropna(), dist="norm", plot=ax4)
        ax4.set_title('Q-Q Plot (Normality Check)')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        filepath = f"{self.output_dir}/7_distribution_analysis.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath

    def create_time_series_trend(self) -> str:
        """Time series showing trends over time"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=90)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Daily average
        daily_avg = df.groupby(df['timestamp'].dt.date)['travel_time_minutes'].mean()

        fig, ax = plt.subplots(figsize=(14, 6))

        ax.plot(daily_avg.index, daily_avg.values, linewidth=1.5, color='#3498db', alpha=0.7)

        # Add rolling average
        rolling_avg = daily_avg.rolling(window=7, center=True).mean()
        ax.plot(rolling_avg.index, rolling_avg.values, linewidth=3, color='#e74c3c',
                label='7-Day Moving Average')

        ax.set_xlabel('Date', fontweight='bold')
        ax.set_ylabel('Average Travel Time (minutes)', fontweight='bold')
        ax.set_title('Traffic Trend Over Time (Last 90 Days)', fontweight='bold', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Rotate dates for better readability
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        filepath = f"{self.output_dir}/8_time_series_trend.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        return filepath


def main():
    """Generate all visualizations for report"""
    print("\n" + "=" * 70)
    print("REPORT VISUALIZATION GENERATOR")
    print("=" * 70)

    db_manager = DatabaseManager()
    generator = ReportVisualizationGenerator(db_manager)

    charts = generator.generate_all_report_charts()

    print("\n" + "=" * 70)
    print("INSTRUCTIONS FOR REPORT")
    print("=" * 70)
    print("""
Include these charts in your assignment report:

1. route_comparison.png - Section: Results & Analysis
   Caption: "Figure 1: Comparison of average travel times across major routes"

2. hourly_pattern.png - Section: Temporal Analysis
   Caption: "Figure 2: 24-hour traffic pattern showing peak periods"

3. weather_impact.png - Section: Environmental Factors
   Caption: "Figure 3: Impact of weather conditions on travel time"

4. peak_offpeak_comparison.png - Section: Statistical Analysis
   Caption: "Figure 4: Distribution comparison between peak and off-peak hours"

5. day_type_comparison.png - Section: Day Type Analysis
   Caption: "Figure 5: Travel time variations across different day types"

6. traffic_heatmap.png - Section: Pattern Analysis
   Caption: "Figure 6: Traffic intensity heatmap by hour and day"

7. distribution_analysis.png - Section: Statistical Validation
   Caption: "Figure 7: Travel time distribution and normality analysis"

8. time_series_trend.png - Section: Trend Analysis
   Caption: "Figure 8: Traffic trends over 90-day period"

TIPS:
- Reference figures in your text: "As shown in Figure 1..."
- Explain what each chart demonstrates
- Discuss patterns and insights from the visualizations
- Use these to support your conclusions
    """)
    print("=" * 70)


if __name__ == "__main__":
    main()