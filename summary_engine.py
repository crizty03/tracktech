
class SummaryEngine:
    def __init__(self):
        pass
    
    def generate_summary(self, rows, metric, query_context):
        """
        Generates a natural language summary based on the data and metric.
        """
        if not rows:
            return "No data found for the given criteria."
            
        # Helper to get column
        def get_col(col):
            return [r[col] for r in rows if r.get(col) is not None]

        insights = []
        
        # General Stats
        total_rows = len(rows)
        
        if metric == 'efficiency':
            vals = get_col('efficiency')
            if vals:
                avg_eff = sum(vals) / len(vals)
                max_eff = max(vals)
                min_eff = min(vals)
                insights.append(f"The average line efficiency was {avg_eff:.2f}%.")
                insights.append(f"The best performance was {max_eff:.2f}% and the lowest was {min_eff:.2f}%.")
            
            # Identify high/low performers if grouped
            if 'buyer_name' in rows[0]:
                # Simple groupby max
                sums = {}
                counts = {}
                for r in rows:
                    if r.get('efficiency') is not None:
                        bn = r['buyer_name']
                        sums[bn] = sums.get(bn, 0) + r['efficiency']
                        counts[bn] = counts.get(bn, 0) + 1
                
                if sums:
                    best_buyer = max(sums, key=lambda k: sums[k]/counts[k])
                    insights.append(f"The best performing buyer was {best_buyer}.")
                
        elif metric == 'wastage':
            vals = get_col('wastage')
            if vals:
                avg_wastage = sum(vals) / len(vals)
                insights.append(f"Average fabric wastage observed is {avg_wastage:.2f}%.")
            
            high_waste = [r for r in rows if r.get('wastage', 0) > 5]
            if high_waste:
                insights.append(f"⚠️ Warning: {len(high_waste)} instances detected with >5% wastage.")
                
        elif metric == 'rejection':
            vals = get_col('total_rejection')
            total_rej = sum(vals)
            insights.append(f"Total rejected pieces found: {total_rej}.")
        
        elif metric == 'production':
             vals = get_col('total_production')
             total_prod = sum(vals)
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
            "data_points": len(rows)
        }

    def get_recommendations(self, metric, rows):
        recs = []
        if metric == 'efficiency':
            vals = [r['efficiency'] for r in rows if r.get('efficiency') is not None]
            if vals and (sum(vals) / len(vals)) < 60:
                recs.append("Efficiency is below 60%. Investigate line bottlenecks and operator training.")
        if metric == 'wastage':
            vals = [r['wastage'] for r in rows if r.get('wastage') is not None]
            if vals and (sum(vals) / len(vals)) > 2:
                recs.append("Fabric wastage > 2%. Check cutting markers and roll utilization.")
        return recs

if __name__ == "__main__":
    # Test
    data = {'efficiency': [75, 80, 55, 90, 60], 'buyer_name': ['H&M', 'Zara', 'Gap', 'H&M', 'Zara']}
    df = pd.DataFrame(data)
    engine = SummaryEngine()
    print(engine.generate_summary(df, 'efficiency', {}))
