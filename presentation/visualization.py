# presentation/visualization.py
# Data visualization service for traffic analysis

# presentation/visualization.py
# Data visualization service for traffic analysis

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path if needed
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from data_access.models import DayType, WeatherCondition
from data_access.database_manager import DatabaseManager
from utilities.logger import get_logger


class TrafficVisualizationService:
    """
    Service for creating various visualizations of traffic data
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(__name__)

        # Set style for better-looking plots
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")

        # Create output directory
        self.output_dir = 'visualizations'
        os.makedirs(self.output_dir, exist_ok=True)

    def create_hourly_traffic_heatmap(self, route_name: Optional[str] = None,
                                      days_back: int = 30) -> str:
        """Create heatmap showing traffic patterns by hour and day of week"""
        try:
            df = self.db_manager.get_traffic_records_dataframe(route_name, days_back)

            if df.empty:
                self.logger.warning("No data available for heatmap")
                return ""

            # Create pivot table
            pivot_data = df.pivot_table(
                values='travel_time_minutes',
                index='hour',
                columns='day_of_week',
                aggfunc='mean'
            )

            # Create figure
            plt.figure(figsize=(12, 8))
            sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlOrRd',
                        cbar_kws={'label': 'Travel Time (minutes)'})

            plt.title(f'Traffic Heatmap - {route_name if route_name else "All Routes"}\n'
                      f'Average Travel Time by Hour and Day', fontsize=14, fontweight='bold')
            plt.xlabel('Day of Week (0=Monday, 6=Sunday)', fontsize=12)
            plt.ylabel('Hour of Day', fontsize=12)

            # Save figure
            filename = f'{self.output_dir}/heatmap_{route_name or "all"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Heatmap saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error creating heatmap: {e}")
            return ""

    def create_route_comparison_chart(self, day_type: DayType, hour: int,
                                      weather: WeatherCondition) -> str:
        """Create bar chart comparing all routes"""
        try:
            routes = self.db_manager.get_all_routes()
            route_names = []
            travel_times = []

            for route in routes:
                analytics = self.db_manager.get_route_analytics(route.name)
                if analytics and analytics.total_records > 0:
                    route_names.append(route.name)
                    travel_times.append(analytics.average_travel_time)

            # Create figure
            fig, ax = plt.subplots(figsize=(12, 6))

            colors = plt.cm.viridis(np.linspace(0, 1, len(route_names)))
            bars = ax.barh(route_names, travel_times, color=colors)

            # Add value labels
            for i, (bar, time) in enumerate(zip(bars, travel_times)):
                ax.text(time + 1, i, f'{time:.1f} min',
                        va='center', fontsize=10, fontweight='bold')

            ax.set_xlabel('Average Travel Time (minutes)', fontsize=12, fontweight='bold')
            ax.set_title('Route Comparison - Average Travel Times',
                         fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)

            # Save figure
            filename = f'{self.output_dir}/route_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Route comparison chart saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error creating route comparison chart: {e}")
            return ""

    def create_traffic_timeline(self, route_name: str, days_back: int = 7) -> str:
        """Create timeline showing traffic patterns over time"""
        try:
            df = self.db_manager.get_traffic_records_dataframe(route_name, days_back)

            if df.empty:
                self.logger.warning(f"No data available for {route_name}")
                return ""

            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

            # Plot 1: Time series of travel times
            ax1.plot(df['timestamp'], df['travel_time_minutes'],
                     marker='o', linestyle='-', linewidth=2, markersize=4, alpha=0.7)
            ax1.fill_between(df['timestamp'], df['travel_time_minutes'],
                             alpha=0.3)
            ax1.set_xlabel('Date & Time', fontsize=12)
            ax1.set_ylabel('Travel Time (minutes)', fontsize=12)
            ax1.set_title(f'{route_name} - Traffic Timeline (Last {days_back} days)',
                          fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

            # Plot 2: Distribution of travel times
            ax2.hist(df['travel_time_minutes'], bins=20, edgecolor='black', alpha=0.7)
            ax2.axvline(df['travel_time_minutes'].mean(), color='red',
                        linestyle='--', linewidth=2, label=f'Mean: {df["travel_time_minutes"].mean():.1f} min')
            ax2.axvline(df['travel_time_minutes'].median(), color='green',
                        linestyle='--', linewidth=2, label=f'Median: {df["travel_time_minutes"].median():.1f} min')
            ax2.set_xlabel('Travel Time (minutes)', fontsize=12)
            ax2.set_ylabel('Frequency', fontsize=12)
            ax2.set_title('Travel Time Distribution', fontsize=12, fontweight='bold')
            ax2.legend()
            ax2.grid(axis='y', alpha=0.3)

            # Save figure
            filename = f'{self.output_dir}/timeline_{route_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Traffic timeline saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error creating traffic timeline: {e}")
            return ""

    def create_weather_impact_chart(self, route_name: str) -> str:
        """Create chart showing impact of weather on travel times"""
        try:
            df = self.db_manager.get_traffic_records_dataframe(route_name, 30)

            if df.empty:
                return ""

            # Group by weather condition
            weather_groups = df.groupby('weather_condition')['travel_time_minutes'].agg(['mean', 'std', 'count'])

            fig, ax = plt.subplots(figsize=(10, 6))

            x = range(len(weather_groups))
            means = weather_groups['mean']
            stds = weather_groups['std']
            labels = weather_groups.index

            bars = ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7,
                          color=['#3498db', '#95a5a6', '#f39c12', '#e74c3c'])

            # Add value labels
            for i, (bar, mean, count) in enumerate(zip(bars, means, weather_groups['count'])):
                ax.text(i, mean + (stds[i] if not pd.isna(stds[i]) else 0) + 2,
                        f'{mean:.1f} min\n(n={int(count)})',
                        ha='center', fontsize=10, fontweight='bold')

            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.set_ylabel('Travel Time (minutes)', fontsize=12, fontweight='bold')
            ax.set_title(f'Weather Impact on Travel Time - {route_name}',
                         fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)

            filename = f'{self.output_dir}/weather_impact_{route_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Weather impact chart saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error creating weather impact chart: {e}")
            return ""

    def create_comprehensive_dashboard(self, route_name: Optional[str] = None) -> str:
        """Create comprehensive dashboard with multiple visualizations"""
        try:
            fig = plt.figure(figsize=(16, 12))
            gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

            df = self.db_manager.get_traffic_records_dataframe(route_name, 30)

            if df.empty:
                self.logger.warning("No data for dashboard")
                return ""

            # 1. Hourly pattern
            ax1 = fig.add_subplot(gs[0, 0])
            hourly_avg = df.groupby('hour')['travel_time_minutes'].mean()
            ax1.plot(hourly_avg.index, hourly_avg.values, marker='o', linewidth=2)
            ax1.fill_between(hourly_avg.index, hourly_avg.values, alpha=0.3)
            ax1.set_title('Average Travel Time by Hour', fontweight='bold')
            ax1.set_xlabel('Hour of Day')
            ax1.set_ylabel('Minutes')
            ax1.grid(True, alpha=0.3)

            # 2. Day of week pattern
            ax2 = fig.add_subplot(gs[0, 1])
            daily_avg = df.groupby('day_of_week')['travel_time_minutes'].mean()
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ax2.bar(range(len(daily_avg)), daily_avg.values, color='steelblue', alpha=0.7)
            ax2.set_xticks(range(7))
            ax2.set_xticklabels(days)
            ax2.set_title('Average Travel Time by Day of Week', fontweight='bold')
            ax2.set_ylabel('Minutes')
            ax2.grid(axis='y', alpha=0.3)

            # 3. Weather impact
            ax3 = fig.add_subplot(gs[1, 0])
            weather_avg = df.groupby('weather_condition')['travel_time_minutes'].mean().sort_values()
            ax3.barh(range(len(weather_avg)), weather_avg.values, color='coral', alpha=0.7)
            ax3.set_yticks(range(len(weather_avg)))
            ax3.set_yticklabels(weather_avg.index)
            ax3.set_title('Impact of Weather Conditions', fontweight='bold')
            ax3.set_xlabel('Average Travel Time (minutes)')
            ax3.grid(axis='x', alpha=0.3)

            # 4. Traffic density distribution
            ax4 = fig.add_subplot(gs[1, 1])
            if 'traffic_density' in df.columns:
                density_counts = df['traffic_density'].value_counts()
                colors_density = {'Light': '#2ecc71', 'Moderate': '#f39c12',
                                  'Heavy': '#e67e22', 'Very Heavy': '#e74c3c'}
                ax4.pie(density_counts.values, labels=density_counts.index,
                        autopct='%1.1f%%', startangle=90,
                        colors=[colors_density.get(d, '#95a5a6') for d in density_counts.index])
                ax4.set_title('Traffic Density Distribution', fontweight='bold')

            # 5. Time series trend
            ax5 = fig.add_subplot(gs[2, :])
            df_sorted = df.sort_values('timestamp')
            ax5.plot(df_sorted['timestamp'], df_sorted['travel_time_minutes'],
                     alpha=0.6, linewidth=1)

            # Add moving average
            window = min(20, len(df_sorted) // 5)
            if window > 1:
                moving_avg = df_sorted['travel_time_minutes'].rolling(window=window).mean()
                ax5.plot(df_sorted['timestamp'], moving_avg, color='red',
                         linewidth=2, label=f'{window}-point Moving Average')
                ax5.legend()

            ax5.set_title('Traffic Trend Over Time', fontweight='bold')
            ax5.set_xlabel('Date & Time')
            ax5.set_ylabel('Travel Time (minutes)')
            ax5.grid(True, alpha=0.3)
            ax5.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45)

            # Main title
            title = f'Traffic Analysis Dashboard - {route_name if route_name else "All Routes"}'
            fig.suptitle(title, fontsize=16, fontweight='bold', y=0.995)

            # Save
            filename = f'{self.output_dir}/dashboard_{route_name or "all"}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Dashboard saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            return ""