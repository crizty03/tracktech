import pandas as pd

class SummaryEngine:
    def __init__(self):
        pass
    
    def generate_summary(self, df, metric, query_context):
        """
        Generates a natural language summary based on the data and metric.
        """
        if df.empty:
            return "No data found for the given criteria."
            
        # Check for NaN values in critical columns if aggregation returned single row with Nulls
        if df.isnull().values.any():
             # Basic check: if all are null, it's empty result
             if df.isnull().all().all():
                 return "No data found for the given criteria."
        
        insights = []
        
        # General Stats
        total_rows = len(df)
        
        if metric == 'efficiency':
            avg_eff = df['efficiency'].mean()
            max_eff = df['efficiency'].max()
            min_eff = df['efficiency'].min()
            insights.append(f"The average line efficiency was {avg_eff:.2f}%.")
            insights.append(f"The best performance was {max_eff:.2f}% and the lowest was {min_eff:.2f}%.")
            
            # Identify high/low performers if grouped
            if 'buyer_name' in df.columns:
                best_buyer = df.groupby('buyer_name')['efficiency'].mean().idxmax()
                insights.append(f"The best performing buyer was {best_buyer}.")
                
        elif metric == 'wastage':
            avg_wastage = df['wastage'].mean()
            insights.append(f"Average fabric wastage observed is {avg_wastage:.2f}%.")
            
            high_waste = df[df['wastage'] > 5]
            if not high_waste.empty:
                insights.append(f"⚠️ Warning: {len(high_waste)} instances detected with >5% wastage.")
                
        elif metric == 'rejection':
            total_rej = df['total_rejection'].sum()
            insights.append(f"Total rejected pieces found: {total_rej}.")
        
        elif metric == 'production':
             total_prod = df['total_production'].sum()
             insights.append(f"Total production quantity is {total_prod:,.0f}.")

        # Recommendations logic
        recommendations = self.get_recommendations(metric, df)
        
        # Contextualize with Query Filters
        if query_context and query_context.get('filters'):
             filters = query_context['filters']
             context_parts = []
             if 'buyer_name' in filters:
                 context_parts.append(f"For Buyer **{filters['buyer_name']}**")
             if 'fabric_type' in filters:
                 context_parts.append(f"For Fabric **{filters['fabric_type']}**")
             
             if context_parts:
                 insights.insert(0, ", ".join(context_parts) + ":")
        
        summary_text = " ".join(insights)
        return {
            "summary": summary_text,
            "recommendations": recommendations,
            "data_points": len(df)
        }

    def get_recommendations(self, metric, df):
        recs = []
        if metric == 'efficiency':
            if df['efficiency'].mean() < 60:
                recs.append("Efficiency is below 60%. Investigate line bottlenecks and operator training.")
        if metric == 'wastage':
            if df['wastage'].mean() > 2:
                recs.append("Fabric wastage > 2%. Check cutting markers and roll utilization.")
        return recs

if __name__ == "__main__":
    # Test
    data = {'efficiency': [75, 80, 55, 90, 60], 'buyer_name': ['H&M', 'Zara', 'Gap', 'H&M', 'Zara']}
    df = pd.DataFrame(data)
    engine = SummaryEngine()
    print(engine.generate_summary(df, 'efficiency', {}))
