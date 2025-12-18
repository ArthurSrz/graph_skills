"""
Generate Data Journalism Report with NetworkX Graph Visualizations
Trump Interview Fact-Check - December 8, 2025
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from neo4j import GraphDatabase
import numpy as np

# Configuration
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "1&Coalplelat"
NEO4J_DATABASE = "neo4j"

OUTPUT_DIR = "/Users/arthursarazin/Documents/graph_skills/examples/trump-fact-check"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

# Color scheme for data journalism
COLORS = {
    'claim': '#E74C3C',        # Red for claims
    'verdict_false': '#C0392B', # Dark red
    'verdict_true': '#27AE60',  # Green
    'verdict_exag': '#F39C12',  # Orange
    'verdict_partial': '#3498DB', # Blue
    'country': '#9B59B6',       # Purple
    'indicator': '#1ABC9C',     # Teal
    'datapoint': '#34495E',     # Dark gray
    'source': '#95A5A6',        # Light gray
}

VERDICT_COLORS = {
    'FALSE': '#E74C3C',
    'TRUE': '#27AE60',
    'EXAGGERATED': '#F39C12',
    'PARTIALLY TRUE': '#3498DB',
    'PARTIAL': '#3498DB',
    'UNVERIFIED': '#95A5A6',
}


def get_driver():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()
    return driver


def create_claim_graph(session, claim_id, title, output_filename):
    """Create a NetworkX visualization for a specific claim."""

    # Query the graph for this claim
    query = """
    MATCH (c:Claim {id: $claim_id})
    OPTIONAL MATCH (c)-[:DEBUNKED_BY]->(d:DebunkSummary)
    OPTIONAL MATCH (c)-[:VERIFIABLE_WITH]->(ind:WorldBankIndicator)
    OPTIONAL MATCH (dp:DataPoint)-[:MEASURES]->(ind)
    OPTIONAL MATCH (dp)-[:FOR_COUNTRY]->(country:Country)
    RETURN c.quote AS quote, c.summary AS summary,
           d.verdict AS verdict, d.reality AS reality,
           ind.name AS indicator_name, ind.id AS indicator_id,
           collect(DISTINCT {country: country.name, value: dp.formatted_value, raw: dp.value}) AS data_points
    """

    result = session.run(query, {"claim_id": claim_id}).single()

    if not result:
        print(f"No data found for {claim_id}")
        return None

    # Create NetworkX graph
    G = nx.DiGraph()

    # Add claim node
    quote = result['quote'][:50] + '...' if result['quote'] and len(result['quote']) > 50 else result['quote']
    G.add_node('claim', label=f"CLAIM\n\"{quote}\"", node_type='claim')

    # Add verdict node
    verdict = result['verdict'] or 'UNVERIFIED'
    G.add_node('verdict', label=f"VERDICT\n{verdict}", node_type=f'verdict_{verdict.lower().replace(" ", "_")}')
    G.add_edge('claim', 'verdict', label='HAS_VERDICT')

    # Add indicator node
    if result['indicator_name']:
        ind_label = result['indicator_name'][:30] + '...' if len(result['indicator_name']) > 30 else result['indicator_name']
        G.add_node('indicator', label=f"INDICATOR\n{ind_label}", node_type='indicator')
        G.add_edge('claim', 'indicator', label='VERIFIABLE_WITH')

        # Add data points (top 5)
        data_points = [dp for dp in result['data_points'] if dp['country']]
        data_points = sorted(data_points, key=lambda x: float(x['raw']) if x['raw'] else 0, reverse=True)[:5]

        for i, dp in enumerate(data_points):
            if dp['country'] and dp['value']:
                node_id = f"data_{i}"
                G.add_node(node_id, label=f"{dp['country']}\n{dp['value']}", node_type='datapoint')
                G.add_edge('indicator', node_id, label='DATA')

    # Create visualization
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    # Layout
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)

    # Adjust positions for better layout
    if 'claim' in pos:
        pos['claim'] = np.array([0, 1])
    if 'verdict' in pos:
        pos['verdict'] = np.array([-0.8, 0.3])
    if 'indicator' in pos:
        pos['indicator'] = np.array([0.8, 0.3])

    # Position data points in a row at bottom
    data_nodes = [n for n in G.nodes() if n.startswith('data_')]
    for i, node in enumerate(data_nodes):
        x = -1 + (2 * i / max(len(data_nodes) - 1, 1))
        pos[node] = np.array([x, -0.5])

    # Draw edges
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#BDC3C7',
                           arrows=True, arrowsize=20,
                           connectionstyle="arc3,rad=0.1",
                           alpha=0.7, width=2)

    # Draw nodes by type
    for node in G.nodes():
        node_type = G.nodes[node].get('node_type', 'default')
        label = G.nodes[node].get('label', node)

        if node_type == 'claim':
            color = COLORS['claim']
            size = 8000
        elif node_type.startswith('verdict'):
            verdict_type = result['verdict'] or 'UNVERIFIED'
            color = VERDICT_COLORS.get(verdict_type, COLORS['verdict_false'])
            size = 6000
        elif node_type == 'indicator':
            color = COLORS['indicator']
            size = 5000
        elif node_type == 'datapoint':
            color = COLORS['datapoint']
            size = 4000
        else:
            color = COLORS['source']
            size = 3000

        nx.draw_networkx_nodes(G, pos, nodelist=[node], ax=ax,
                               node_color=color, node_size=size,
                               alpha=0.9)

        # Add labels
        x, y = pos[node]
        ax.annotate(label, xy=(x, y), ha='center', va='center',
                   fontsize=9, fontweight='bold', color='white',
                   wrap=True)

    # Title
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color='#2C3E50')

    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['claim'], label='Trump Claim'),
        mpatches.Patch(facecolor=VERDICT_COLORS['FALSE'], label='Verdict: FALSE'),
        mpatches.Patch(facecolor=VERDICT_COLORS['TRUE'], label='Verdict: TRUE'),
        mpatches.Patch(facecolor=VERDICT_COLORS['EXAGGERATED'], label='Verdict: EXAGGERATED'),
        mpatches.Patch(facecolor=COLORS['indicator'], label='World Bank Indicator'),
        mpatches.Patch(facecolor=COLORS['datapoint'], label='Data Point'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', framealpha=0.9)

    ax.axis('off')
    plt.tight_layout()

    # Save
    filepath = os.path.join(IMAGES_DIR, output_filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close()

    print(f"Created: {filepath}")
    return {
        'quote': result['quote'],
        'summary': result['summary'],
        'verdict': verdict,
        'reality': result['reality'],
        'indicator': result['indicator_name'],
        'data_points': data_points if result['indicator_name'] else []
    }


def create_overview_graph(session, output_filename):
    """Create an overview graph showing all claims and their verdicts."""

    query = """
    MATCH (c:Claim)
    OPTIONAL MATCH (c)-[:DEBUNKED_BY]->(d:DebunkSummary)
    RETURN c.id AS id, c.summary AS summary, d.verdict AS verdict
    ORDER BY c.id
    """

    results = session.run(query).data()

    G = nx.DiGraph()

    # Central node
    G.add_node('interview', label='Trump Interview\nDec 8, 2025', node_type='source')

    # Add claims
    for r in results:
        claim_id = r['id']
        summary = r['summary'][:25] + '...' if r['summary'] and len(r['summary']) > 25 else r['summary']
        verdict = r['verdict'] or 'UNVERIFIED'

        G.add_node(claim_id, label=f"{summary}\n[{verdict}]",
                   node_type=f'verdict_{verdict.lower().replace(" ", "_")}',
                   verdict=verdict)
        G.add_edge('interview', claim_id)

    # Create visualization
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    # Circular layout
    pos = nx.spring_layout(G, k=2, iterations=100, seed=42)
    pos['interview'] = np.array([0, 0])

    # Arrange claims in a circle
    claims = [n for n in G.nodes() if n != 'interview']
    for i, claim in enumerate(claims):
        angle = 2 * np.pi * i / len(claims)
        pos[claim] = np.array([1.5 * np.cos(angle), 1.5 * np.sin(angle)])

    # Draw edges
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='#BDC3C7',
                           arrows=True, arrowsize=15, alpha=0.5, width=1.5)

    # Draw nodes
    for node in G.nodes():
        if node == 'interview':
            color = '#2C3E50'
            size = 10000
        else:
            verdict = G.nodes[node].get('verdict', 'UNVERIFIED')
            color = VERDICT_COLORS.get(verdict, '#95A5A6')
            size = 6000

        nx.draw_networkx_nodes(G, pos, nodelist=[node], ax=ax,
                               node_color=color, node_size=size, alpha=0.9)

        label = G.nodes[node].get('label', node)
        x, y = pos[node]
        ax.annotate(label, xy=(x, y), ha='center', va='center',
                   fontsize=8, fontweight='bold', color='white')

    ax.set_title('Trump Interview Fact-Check Overview\nPolitico "The Conversation" - December 8, 2025',
                 fontsize=18, fontweight='bold', pad=20, color='#2C3E50')

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=VERDICT_COLORS['FALSE'], label='FALSE (4)'),
        mpatches.Patch(facecolor=VERDICT_COLORS['TRUE'], label='TRUE (1)'),
        mpatches.Patch(facecolor=VERDICT_COLORS['EXAGGERATED'], label='EXAGGERATED (1)'),
        mpatches.Patch(facecolor=VERDICT_COLORS['PARTIAL'], label='PARTIALLY TRUE (2)'),
        mpatches.Patch(facecolor='#95A5A6', label='UNVERIFIED'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', framealpha=0.9, fontsize=10)

    ax.axis('off')
    plt.tight_layout()

    filepath = os.path.join(IMAGES_DIR, output_filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close()

    print(f"Created: {filepath}")


def create_comparison_bar_chart(data, title, xlabel, output_filename, highlight_claim=None):
    """Create a bar chart comparing values across countries."""

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    countries = [d['country'] for d in data]
    values = [float(d['raw']) for d in data]

    # Color bars - highlight specific ones
    colors = ['#3498DB' if c != highlight_claim else '#E74C3C' for c in countries]

    bars = ax.barh(countries, values, color=colors, alpha=0.8, edgecolor='white', linewidth=2)

    # Add value labels
    for bar, val in zip(bars, values):
        if val >= 1000000000:
            label = f"${val/1e9:.1f}B"
        elif val >= 1000000:
            label = f"{val/1e6:.1f}M"
        elif val >= 1:
            label = f"{val:.2f}"
        else:
            label = f"{val:.4f}"
        ax.text(bar.get_width() + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                label, va='center', fontsize=11, fontweight='bold', color='#2C3E50')

    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold', color='#2C3E50')
    ax.set_title(title, fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#BDC3C7')
    ax.spines['bottom'].set_color('#BDC3C7')
    ax.tick_params(colors='#2C3E50')

    plt.tight_layout()

    filepath = os.path.join(IMAGES_DIR, output_filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    plt.close()

    print(f"Created: {filepath}")


def main():
    """Generate all visualizations and the report."""

    print("=" * 60)
    print("GENERATING DATA JOURNALISM REPORT")
    print("=" * 60)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    driver = get_driver()

    with driver.session(database=NEO4J_DATABASE) as session:

        # 1. Overview graph
        print("\n[1/8] Creating overview graph...")
        create_overview_graph(session, "00_overview.png")

        # 2. Sweden crime claim
        print("\n[2/8] Creating Sweden crime graph...")
        sweden_data = create_claim_graph(session, "CLAIM_010",
                                         "Claim: Sweden is 'Very Unsafe'",
                                         "01_sweden_crime.png")

        # Get crime data for bar chart
        crime_query = """
        MATCH (dp:DataPoint)-[:FOR_COUNTRY]->(c:Country)
        WHERE dp.indicator = 'Intentional homicides (per 100,000 people)'
        RETURN c.name AS country, dp.value AS raw, dp.formatted_value AS value
        ORDER BY dp.value DESC
        """
        crime_data = session.run(crime_query).data()
        if crime_data:
            create_comparison_bar_chart(crime_data,
                                       "Homicide Rates per 100,000 (2021)",
                                       "Homicides per 100,000 people",
                                       "01b_crime_comparison.png",
                                       highlight_claim="Sweden")

        # 3. Germany crime claim
        print("\n[3/8] Creating Germany crime graph...")
        create_claim_graph(session, "CLAIM_011",
                          "Claim: Germany was 'Crime-Free'",
                          "02_germany_crime.png")

        # 4. $18 trillion claim
        print("\n[4/8] Creating $18 trillion graph...")
        fdi_data = create_claim_graph(session, "CLAIM_005",
                                      "Claim: '$18 Trillion Coming Into Our Country'",
                                      "03_18_trillion.png")

        # FDI bar chart
        fdi_query = """
        MATCH (dp:DataPoint)-[:FOR_COUNTRY]->(c:Country)
        WHERE dp.indicator CONTAINS 'Foreign direct investment'
        RETURN c.name AS country, dp.value AS raw, dp.formatted_value AS value
        ORDER BY dp.value DESC
        """
        fdi_data_chart = session.run(fdi_query).data()
        if fdi_data_chart:
            create_comparison_bar_chart(fdi_data_chart,
                                       "Foreign Direct Investment Inflows (2024)",
                                       "FDI (US$)",
                                       "03b_fdi_comparison.png")

        # 5. $350 billion Ukraine claim
        print("\n[5/8] Creating Ukraine aid graph...")
        create_claim_graph(session, "CLAIM_014",
                          "Claim: 'Biden Gave Ukraine $350 Billion'",
                          "04_ukraine_aid.png")

        # 6. NATO 5% claim
        print("\n[6/8] Creating NATO spending graph...")
        create_claim_graph(session, "CLAIM_012",
                          "Claim: 'NATO Spending at 5% GDP'",
                          "05_nato_spending.png")

        # NATO bar chart
        nato_query = """
        MATCH (dp:DataPoint)-[:FOR_COUNTRY]->(c:Country)
        WHERE dp.indicator CONTAINS 'Military expenditure (% of GDP)'
        RETURN c.name AS country, dp.value AS raw, dp.formatted_value AS value
        ORDER BY dp.value DESC
        """
        nato_data = session.run(nato_query).data()
        if nato_data:
            create_comparison_bar_chart(nato_data,
                                       "Military Expenditure as % of GDP (2023)",
                                       "% of GDP",
                                       "05b_nato_comparison.png")

        # 7. Russia size claim
        print("\n[7/8] Creating Russia size graph...")
        create_claim_graph(session, "CLAIM_016",
                          "Claim: 'Russia is Much Bigger'",
                          "06_russia_size.png")

        # Population bar chart
        pop_query = """
        MATCH (dp:DataPoint)-[:FOR_COUNTRY]->(c:Country)
        WHERE dp.indicator = 'Population, total'
        RETURN c.name AS country, dp.value AS raw, dp.formatted_value AS value
        ORDER BY dp.value DESC
        """
        pop_data = session.run(pop_query).data()
        if pop_data:
            create_comparison_bar_chart(pop_data,
                                       "Population Comparison (2023)",
                                       "Population",
                                       "06b_population_comparison.png")

        # 8. Immigration claim
        print("\n[8/8] Creating immigration graph...")
        create_claim_graph(session, "CLAIM_013",
                          "Claim: 'Tremendous Immigration to Europe'",
                          "07_immigration.png")

        # Migration bar chart
        mig_query = """
        MATCH (dp:DataPoint)-[:FOR_COUNTRY]->(c:Country)
        WHERE dp.indicator = 'Net migration'
        RETURN c.name AS country, dp.value AS raw, dp.formatted_value AS value
        ORDER BY dp.value DESC
        """
        mig_data = session.run(mig_query).data()
        if mig_data:
            create_comparison_bar_chart(mig_data,
                                       "Net Migration by Country (2022)",
                                       "Net Migration",
                                       "07b_migration_comparison.png")

    driver.close()

    print("\n" + "=" * 60)
    print("ALL VISUALIZATIONS CREATED")
    print(f"Output directory: {IMAGES_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
