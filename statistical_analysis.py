# statistical_analysis.py
# Statistical analysis and reporting for assignment documentation
# Generates comprehensive statistics for the report

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import json
from scipy import stats
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from data_access.database_manager import DatabaseManager
from data_access.models import DayType, WeatherCondition, TrafficDensity
from utilities.logger import get_logger


class StatisticalAnalyzer:
    """
    Comprehensive statistical analysis for traffic data.
    Generates reports suitable for academic assignment documentation.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = get_logger(__name__)

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate complete statistical report covering all aspects.

        Returns:
            Dictionary containing all statistical analyses
        """
        self.logger.info("Generating comprehensive statistical report...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'database_overview': self._get_database_overview(),
            'descriptive_statistics': self._calculate_descriptive_stats(),
            'route_comparison': self._compare_routes_statistically(),
            'temporal_analysis': self._analyze_temporal_patterns(),
            'weather_impact': self._analyze_weather_impact(),
            'peak_hour_analysis': self._detailed_peak_analysis(),
            'day_type_comparison': self._compare_day_types(),
            'prediction_accuracy': self._evaluate_prediction_accuracy(),
            'correlation_analysis': self._correlation_analysis()
        }

        self.logger.info("Statistical report generation complete")
        return report

    def _get_database_overview(self) -> Dict[str, Any]:
        """Get overview of database contents"""
        stats = self.db_manager.get_database_stats()

        return {
            'total_routes': stats['routes_count'],
            'total_records': stats['records_count'],
            'date_range': {
                'start': stats['earliest_record'],
                'end': stats['latest_record']
            },
            'database_size_mb': round(stats['database_size_mb'], 2),
            'records_per_route': stats['records_count'] // stats['routes_count']
            if stats['routes_count'] > 0 else 0
        }

    def _calculate_descriptive_stats(self) -> Dict[str, Any]:
        """
        Calculate descriptive statistics for all routes.
        Mean, median, mode, standard deviation, variance, etc.
        """
        routes = self.db_manager.get_all_routes()
        all_stats = {}

        for route in routes:
            df = self.db_manager.get_traffic_records_dataframe(route.name, days_back=90)

            if df.empty:
                continue

            travel_times = df['travel_time_minutes'].values

            stats_dict = {
                'count': len(travel_times),
                'mean': float(np.mean(travel_times)),
                'median': float(np.median(travel_times)),
                'mode': float(stats.mode(travel_times)[0]) if len(travel_times) > 0 else 0,
                'std_dev': float(np.std(travel_times)),
                'variance': float(np.var(travel_times)),
                'min': float(np.min(travel_times)),
                'max': float(np.max(travel_times)),
                'range': float(np.ptp(travel_times)),
                'q1': float(np.percentile(travel_times, 25)),
                'q3': float(np.percentile(travel_times, 75)),
                'iqr': float(np.percentile(travel_times, 75) - np.percentile(travel_times, 25)),
                'coefficient_of_variation': float(np.std(travel_times) / np.mean(travel_times) * 100)
                if np.mean(travel_times) > 0 else 0,
                'skewness': float(stats.skew(travel_times)),
                'kurtosis': float(stats.kurtosis(travel_times))
            }

            all_stats[route.name] = stats_dict

        return all_stats

    def _compare_routes_statistically(self) -> Dict[str, Any]:
        """
        Statistical comparison between routes.
        Uses ANOVA and t-tests.
        """
        routes = self.db_manager.get_all_routes()
        route_data = []
        route_names = []

        for route in routes[:6]:  # Compare first 6 routes
            df = self.db_manager.get_traffic_records_dataframe(route.name, days_back=90)
            if not df.empty:
                route_data.append(df['travel_time_minutes'].values)
                route_names.append(route.name)

        if len(route_data) < 2:
            return {'error': 'Insufficient routes for comparison'}

        # ANOVA test
        f_stat, p_value = stats.f_oneway(*route_data)

        # Pairwise comparisons
        pairwise_results = []
        for i in range(len(route_data)):
            for j in range(i + 1, len(route_data)):
                t_stat, p_val = stats.ttest_ind(route_data[i], route_data[j])
                pairwise_results.append({
                    'route1': route_names[i],
                    'route2': route_names[j],
                    't_statistic': float(t_stat),
                    'p_value': float(p_val),
                    'significant': p_val < 0.05,
                    'mean_difference': float(np.mean(route_data[i]) - np.mean(route_data[j]))
                })

        return {
            'anova': {
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'interpretation': 'Significant differences exist between routes'
                if p_value < 0.05 else 'No significant differences'
            },
            'pairwise_comparisons': pairwise_results
        }

    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across time (hourly, daily, weekly)"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=90)

        if df.empty:
            return {'error': 'No data available'}

        # Hourly patterns
        hourly_stats = df.groupby('hour')['travel_time_minutes'].agg([
            ('mean', 'mean'),
            ('std', 'std'),
            ('count', 'count'),
            ('min', 'min'),
            ('max', 'max')
        ]).to_dict('index')

        # Convert to serializable format
        hourly_stats = {int(k): {key: float(v) for key, v in val.items()}
                        for k, val in hourly_stats.items()}

        # Day of week patterns
        daily_stats = df.groupby('day_of_week')['travel_time_minutes'].agg([
            ('mean', 'mean'),
            ('std', 'std'),
            ('count', 'count')
        ]).to_dict('index')

        daily_stats = {int(k): {key: float(v) for key, v in val.items()}
                       for k, val in daily_stats.items()}

        # Identify peak and off-peak hours
        hourly_means = df.groupby('hour')['travel_time_minutes'].mean()
        peak_hours = hourly_means[hourly_means > hourly_means.mean() + hourly_means.std()].index.tolist()
        offpeak_hours = hourly_means[hourly_means < hourly_means.mean() - hourly_means.std()].index.tolist()

        return {
            'hourly_patterns': hourly_stats,
            'daily_patterns': daily_stats,
            'peak_hours': [int(h) for h in peak_hours],
            'offpeak_hours': [int(h) for h in offpeak_hours],
            'busiest_hour': int(hourly_means.idxmax()),
            'quietest_hour': int(hourly_means.idxmin()),
            'busiest_day': int(df.groupby('day_of_week')['travel_time_minutes'].mean().idxmax()),
            'quietest_day': int(df.groupby('day_of_week')['travel_time_minutes'].mean().idxmin())
        }

    def _analyze_weather_impact(self) -> Dict[str, Any]:
        """Analyze impact of weather on travel times"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=90)

        if df.empty:
            return {'error': 'No data available'}

        # Group by weather condition
        weather_stats = df.groupby('weather_condition')['travel_time_minutes'].agg([
            ('mean', 'mean'),
            ('std', 'std'),
            ('count', 'count'),
            ('median', 'median')
        ]).to_dict('index')

        # Calculate impact percentages
        clear_mean = weather_stats.get('Clear', {}).get('mean', 0)

        weather_impact = {}
        for condition, stats_dict in weather_stats.items():
            mean_time = stats_dict['mean']
            impact_pct = ((mean_time - clear_mean) / clear_mean * 100) if clear_mean > 0 else 0

            weather_impact[condition] = {
                'mean_time': float(mean_time),
                'std_dev': float(stats_dict['std']),
                'count': int(stats_dict['count']),
                'median_time': float(stats_dict['median']),
                'impact_percentage': float(impact_pct),
                'delay_minutes': float(mean_time - clear_mean) if clear_mean > 0 else 0
            }

        # Statistical test for weather impact
        clear_data = df[df['weather_condition'] == 'Clear']['travel_time_minutes'].values
        rainy_data = df[df['weather_condition'].isin(['Rainy', 'Heavy Rain'])]['travel_time_minutes'].values

        if len(clear_data) > 0 and len(rainy_data) > 0:
            t_stat, p_value = stats.ttest_ind(clear_data, rainy_data)
            weather_impact['statistical_test'] = {
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'significant': p_value < 0.05,
                'interpretation': 'Weather has significant impact on travel time'
                if p_value < 0.05 else 'Weather impact not statistically significant'
            }

        return weather_impact

    def _detailed_peak_analysis(self) -> Dict[str, Any]:
        """Detailed analysis of peak vs off-peak periods"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=90)

        if df.empty:
            return {'error': 'No data available'}

        # Define peak hours (7-9 AM, 5-7 PM)
        df['is_peak'] = df['hour'].isin([7, 8, 17, 18])

        peak_data = df[df['is_peak']]['travel_time_minutes']
        offpeak_data = df[~df['is_peak']]['travel_time_minutes']

        # Statistical comparison
        t_stat, p_value = stats.ttest_ind(peak_data, offpeak_data)

        return {
            'peak_hours': {
                'mean': float(peak_data.mean()),
                'median': float(peak_data.median()),
                'std_dev': float(peak_data.std()),
                'count': int(len(peak_data))
            },
            'offpeak_hours': {
                'mean': float(offpeak_data.mean()),
                'median': float(offpeak_data.median()),
                'std_dev': float(offpeak_data.std()),
                'count': int(len(offpeak_data))
            },
            'comparison': {
                'mean_difference': float(peak_data.mean() - offpeak_data.mean()),
                'percentage_increase': float((peak_data.mean() - offpeak_data.mean()) / offpeak_data.mean() * 100),
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'significant': p_value < 0.05
            }
        }

    def _compare_day_types(self) -> Dict[str, Any]:
        """Compare weekday vs weekend vs rainy day traffic"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=90)

        if df.empty:
            return {'error': 'No data available'}

        day_type_stats = df.groupby('day_type')['travel_time_minutes'].agg([
            ('mean', 'mean'),
            ('std', 'std'),
            ('count', 'count'),
            ('median', 'median'),
            ('min', 'min'),
            ('max', 'max')
        ]).to_dict('index')

        # Convert to serializable format
        day_type_stats = {k: {key: float(v) for key, v in val.items()}
                          for k, val in day_type_stats.items()}

        # Calculate percentage differences
        weekday_mean = day_type_stats.get('Week Day', {}).get('mean', 0)

        for day_type, stats_dict in day_type_stats.items():
            if day_type != 'Week Day' and weekday_mean > 0:
                diff = ((stats_dict['mean'] - weekday_mean) / weekday_mean * 100)
                stats_dict['vs_weekday_percent'] = float(diff)

        return day_type_stats

    def _evaluate_prediction_accuracy(self) -> Dict[str, Any]:
        """
        Evaluate prediction accuracy using holdout test.
        Split data into train/test and measure accuracy.
        """
        routes = self.db_manager.get_all_routes()
        accuracy_results = {}

        for route in routes[:5]:  # Test first 5 routes
            df = self.db_manager.get_traffic_records_dataframe(route.name, days_back=90)

            if len(df) < 20:
                continue

            # Sort by timestamp
            df = df.sort_values('timestamp')

            # Split 80/20
            split_idx = int(len(df) * 0.8)
            train_data = df.iloc[:split_idx]
            test_data = df.iloc[split_idx:]

            # Simple prediction: use training mean for prediction
            predicted_mean = train_data['travel_time_minutes'].mean()

            # Calculate errors
            actual_values = test_data['travel_time_minutes'].values
            predictions = np.full(len(actual_values), predicted_mean)

            mae = float(np.mean(np.abs(actual_values - predictions)))
            rmse = float(np.sqrt(np.mean((actual_values - predictions) ** 2)))
            mape = float(np.mean(np.abs((actual_values - predictions) / actual_values)) * 100)

            # Accuracy (within 20% considered accurate)
            within_20pct = np.abs((actual_values - predictions) / actual_values) <= 0.2
            accuracy_pct = float(np.mean(within_20pct) * 100)

            accuracy_results[route.name] = {
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'accuracy_percentage': accuracy_pct,
                'test_samples': len(test_data),
                'mean_actual': float(np.mean(actual_values)),
                'mean_predicted': float(predicted_mean)
            }

        # Overall statistics
        if accuracy_results:
            all_maes = [r['mae'] for r in accuracy_results.values()]
            all_accuracies = [r['accuracy_percentage'] for r in accuracy_results.values()]

            accuracy_results['overall'] = {
                'average_mae': float(np.mean(all_maes)),
                'average_accuracy': float(np.mean(all_accuracies)),
                'routes_tested': len(accuracy_results) - 1
            }

        return accuracy_results

    def _correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between variables"""
        df = self.db_manager.get_traffic_records_dataframe(days_back=90)

        if df.empty:
            return {'error': 'No data available'}

        # Create numerical encoding for categorical variables
        df['weather_code'] = df['weather_condition'].map({
            'Clear': 0, 'Cloudy': 1, 'Rainy': 2, 'Heavy Rain': 3
        })

        df['day_type_code'] = df['day_type'].map({
            'Week Day': 0, 'Weekend Day': 1, 'Raine Day': 2
        })

        # Calculate correlations
        correlations = {}

        if 'weather_code' in df.columns:
            corr = df['travel_time_minutes'].corr(df['weather_code'])
            correlations['weather_vs_time'] = {
                'correlation': float(corr),
                'interpretation': 'Strong' if abs(corr) > 0.7 else 'Moderate' if abs(corr) > 0.3 else 'Weak'
            }

        if 'hour' in df.columns:
            corr = df['travel_time_minutes'].corr(df['hour'])
            correlations['hour_vs_time'] = {
                'correlation': float(corr),
                'interpretation': 'Strong' if abs(corr) > 0.7 else 'Moderate' if abs(corr) > 0.3 else 'Weak'
            }

        if 'day_of_week' in df.columns:
            corr = df['travel_time_minutes'].corr(df['day_of_week'])
            correlations['day_vs_time'] = {
                'correlation': float(corr),
                'interpretation': 'Strong' if abs(corr) > 0.7 else 'Moderate' if abs(corr) > 0.3 else 'Weak'
            }

        return correlations

    def export_report_to_json(self, filepath: str = 'outputs/reports/statistical_report.json'):
        """Export comprehensive report to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        report = self.generate_comprehensive_report()

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Report exported to {filepath}")
        return filepath

    def generate_summary_table(self) -> pd.DataFrame:
        """Generate summary table suitable for report"""
        routes = self.db_manager.get_all_routes()
        summary_data = []

        for route in routes:
            analytics = self.db_manager.get_route_analytics(route.name)
            if analytics and analytics.total_records > 0:
                summary_data.append({
                    'Route': route.name,
                    'Avg Time (min)': round(analytics.average_travel_time, 1),
                    'Min Time (min)': analytics.min_travel_time,
                    'Max Time (min)': analytics.max_travel_time,
                    'Peak Avg (min)': round(analytics.peak_hour_average, 1),
                    'Off-Peak Avg (min)': round(analytics.off_peak_average, 1),
                    'Weekend Avg (min)': round(analytics.weekend_average, 1),
                    'Variability (%)': round(analytics.get_variability(), 1),
                    'Records': analytics.total_records
                })

        return pd.DataFrame(summary_data)


def main():
    """Generate and display statistical report"""
    print("=" * 70)
    print("TRAFFIC ANALYSIS - STATISTICAL REPORT GENERATOR")
    print("=" * 70)

    db_manager = DatabaseManager()
    analyzer = StatisticalAnalyzer(db_manager)

    print("\nGenerating comprehensive statistical report...")
    report = analyzer.generate_comprehensive_report()

    print("\n" + "=" * 70)
    print("DATABASE OVERVIEW")
    print("=" * 70)
    overview = report['database_overview']
    print(f"Total Routes: {overview['total_routes']}")
    print(f"Total Records: {overview['total_records']:,}")
    print(f"Records per Route: {overview['records_per_route']}")
    print(f"Database Size: {overview['database_size_mb']} MB")

    print("\n" + "=" * 70)
    print("ROUTE SUMMARY TABLE")
    print("=" * 70)
    summary_table = analyzer.generate_summary_table()
    print(summary_table.to_string(index=False))

    print("\n" + "=" * 70)
    print("WEATHER IMPACT ANALYSIS")
    print("=" * 70)
    weather = report['weather_impact']
    for condition, stats in weather.items():
        if condition != 'statistical_test' and isinstance(stats, dict):
            print(f"\n{condition}:")
            print(f"  Mean Time: {stats['mean_time']:.1f} min")
            print(f"  Impact: {stats['impact_percentage']:+.1f}%")
            print(f"  Delay: {stats['delay_minutes']:+.1f} min")

    print("\n" + "=" * 70)
    print("PEAK VS OFF-PEAK COMPARISON")
    print("=" * 70)
    peak_analysis = report['peak_hour_analysis']
    if 'comparison' in peak_analysis:
        comp = peak_analysis['comparison']
        print(f"Peak Hours Mean: {peak_analysis['peak_hours']['mean']:.1f} min")
        print(f"Off-Peak Mean: {peak_analysis['offpeak_hours']['mean']:.1f} min")
        print(f"Difference: {comp['mean_difference']:.1f} min ({comp['percentage_increase']:.1f}% increase)")
        print(f"Statistical Significance: {'Yes' if comp['significant'] else 'No'} (p={comp['p_value']:.4f})")

    # Export to JSON
    filepath = analyzer.export_report_to_json()
    print(f"\n\nFull report exported to: {filepath}")
    print("=" * 70)


if __name__ == "__main__":
    main()