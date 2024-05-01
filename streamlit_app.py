
import streamlit as st
import pandas as pd
import networkx as nx
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import matplotlib.pyplot as plt  # Import matplotlib for graph visualization


# Improved styling for Streamlit components

st.set_page_config(layout="wide", page_title="Semiconductor Ecosystem")
def set_custom_styles():
    st.markdown("""
        <style>
        .stButton>button {
            color: white;
            border: 2px solid #4CAF50;
            padding: 10px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            background-color: #4CAF50;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stSelectbox>div>div>select {
            padding: 10px;
            border-radius: 20px;
            border: 1px solid #CCC;
        }
        .stMultiselect>div>div>div>select {
            padding: 10px;
            border-radius: 20px;
        }
        .css-1cpxqw2 {
            border-radius: 20px;
        }
        .css-1yjuwjr {
            padding: 8px 16px;
            border-radius: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    

# Function to load data from CSV files
def load_csv_data():
    challenge_df = pd.read_csv("challenge.csv")
    tools_df = pd.read_csv("tool.csv")
    matrix_df = pd.read_csv("matrix.csv")
    gpt_df = pd.read_csv("gpt.csv")  # Assuming you have a gpt.csv for the graph
    info_df = pd.read_csv("info.csv")  # Load info.csv here
    innovation_df = pd.read_csv("innovation.csv")  # Load innovation.csv here
    return challenge_df, tools_df, matrix_df, gpt_df, info_df, innovation_df

def load_network_graph(gpt_df, forbidden_nodes=None):
    G = nx.from_pandas_edgelist(gpt_df, 'source', 'target', create_using=nx.DiGraph())
    if forbidden_nodes:
        G.remove_nodes_from(forbidden_nodes)  # Remove the specified forbidden nodes from the graph
    return G

# New TSP-based shortest path finding function using OR-Tools
def solve_tsp_with_or_tools(G, selected_nodes, forbidden_nodes):
    # Ensure selected_nodes are actually in G and not in forbidden_nodes
    selected_nodes = [node for node in selected_nodes if node in G and node not in forbidden_nodes]

    # Pre-sort selected_nodes to prioritize nodes starting with "G"
    selected_nodes.sort(key=lambda x: (not x.startswith('G'), x))

    node_to_index = {node: i for i, node in enumerate(selected_nodes)}
    index_to_node = {i: node for node, i in node_to_index.items()}

    num_nodes = len(selected_nodes)
    distance_matrix = []

    for i in range(num_nodes):
        distances_row = []
        for j in range(num_nodes):
            if i == j:
                distances_row.append(0)
            else:
                try:
                    path_length = nx.shortest_path_length(G, source=selected_nodes[i], target=selected_nodes[j], weight='weight', method='dijkstra')
                    distances_row.append(path_length)
                except nx.NetworkXNoPath:
                    st.error(f"Node {selected_nodes[j]} not reachable from {selected_nodes[i]}. Please rethink the forbidden nodes.")
                    return None
        distance_matrix.append(distances_row)

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(index_to_node[node_index])
            index = solution.Value(routing.NextVar(index))
        full_path = []
        for i in range(len(route) - 1):
            path = nx.shortest_path(G, source=route[i], target=route[i+1], weight='weight')
            full_path.extend(path[:-1])
        full_path.append(route[-1])
        return full_path
    else:
        st.error("No complete path found. Please reconsider the selected and forbidden nodes.")
        return None

# Function to visualize the shortest path
def visualize_shortest_path(G, path):
    # Use Kamada-Kawai layout for better node distribution in complex graphs
    pos = nx.kamada_kawai_layout(G)
    plt.figure(figsize=(12, 8))

    # Draw the full graph with lighter and thinner edges and smaller nodes
    nx.draw(G, pos, with_labels=False, node_color='lightblue', edge_color='gray', width=0.5, node_size=200, alpha=0.6)

    # Highlight the path in the graph
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_nodes(G, pos, nodelist=path, node_color='red', node_size=250)
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='red', width=2, alpha=0.9)

    # Draw labels only for the nodes in the path
    path_labels = {n: n for n in path}
    nx.draw_networkx_labels(G, pos, labels=path_labels, font_color='black')

    plt.title("Shortest Path Visualization")
    plt.axis('off')
    st.pyplot(plt)

# Function to display filtered info from info.csv based on the shortest path
def display_filtered_info(info_df, path):
    # Reorder info_df to match the order of nodes in the path
    # Create a temporary column 'order' to store the order based on the path
    info_df['order'] = info_df['source'].apply(lambda x: path.index(x) if x in path else -1)

    # Filter out rows where 'source' is not in the path (i.e., 'order' is -1)
    filtered_info = info_df[info_df['order'] != -1]

    # Sort the DataFrame based on the 'order' column
    filtered_info_sorted = filtered_info.sort_values(by='order')

    # Drop the 'order' column as it's no longer needed
    filtered_info_sorted = filtered_info_sorted.drop(columns=['order'])

    # Display the sorted table
    st.table(filtered_info_sorted[['institution', 'tool', 'Description', 'KPI']])

# Function to display challenge analysis options and corresponding tools
def display_challenge_analysis(challenge_df, tools_df, matrix_df, gpt_df, info_df, innovation_df):
    col1, col2, col3 = st.columns([3,2,3])
    with col2:
        if st.button("Show Challenges", key="show_challenges_button"):
            st.session_state.show_challenges = True

    if st.session_state.get('show_challenges', False):
        # Added centered, larger font size line "Step 1/3: Select Challenges & Tools" before the player filter
        st.markdown("<h2 style='text-align: center;'>Step 1/3: Select Player, Challenges & Tools</h2>", unsafe_allow_html=True)
        
        player_options = ['All'] + list(challenge_df['player'].unique())
        selected_player = st.selectbox("Player", options=player_options, index=0, key='selected_player')

        cat2_options = ['All'] + list(challenge_df['cat 2'].unique())
        selected_cat2 = st.selectbox("Challenge type", options=cat2_options, index=0, key='selected_cat2')

        if selected_player != 'All' and selected_cat2 != 'All':
            if selected_player != 'All':
                challenge_df = challenge_df[challenge_df['player'] == selected_player]
            if selected_cat2 != 'All':
                challenge_df = challenge_df[challenge_df['cat 2'] == selected_cat2]

            st.write("Select Challenges:")
            challenges = challenge_df['challenge'].unique()
            selected_challenges = []
            col1, col2 = st.columns(2)
            half_len = len(challenges) // 2 + len(challenges) % 2
            for i, challenge in enumerate(challenges):
                with col1 if i < half_len else col2:
                    # Corrected the use of curly braces for the checkbox key
                    if st.checkbox(challenge, key=f'checkbox_{challenge}'):
                        selected_challenges.append(challenge)

            if selected_challenges:
                st.write("Tools for Selected Challenges:")
                filtered_tools = tools_df
                cols = ['Consumers of semiconductors', 'Education and Research Institutions', 'Financial & Legal', 'Industry Associations and Alliances', 'Government & Regulators', 'Semiconductor manufacturing']
                selected_tools = {col: [] for col in cols}
                stored_values = []

                # First row: Four columns for the first four sections
                grid_cols = st.columns(4)
                for index, col in enumerate(cols[:4]):
                    with grid_cols[index]:
                        st.markdown(f"#### {col}")
                        st.markdown("<hr>", unsafe_allow_html=True)
                        values = filtered_tools[col].dropna().unique()
                        for value in values:
                            default_selected = value in filtered_tools[filtered_tools['risk'].isin(selected_challenges)][col].unique()
                            if st.checkbox(f"{value}", key=f'{col}_{value}', value=default_selected):
                                selected_tools[col].append(value)
                                stored_values.append(f"{col}{value}")

                # Second row: "Government & Regulators" and "Semiconductor manufacturing" with centered titles
                st.markdown("<hr>", unsafe_allow_html=True)  # Optional: add a separator for visual distinction
                second_row_cols = st.columns(2)
                for index, col in enumerate(cols[4:]):
                    with second_row_cols[index]:
                        # Use HTML for center-aligned header
                        st.markdown(f"<h4 style='text-align: center;'>{col}</h4>", unsafe_allow_html=True)
                        nested_cols = st.columns(2)  # Create two columns under each centered header
                        values = filtered_tools[col].dropna().unique()
                        half_len = len(values) // 2 + len(values) % 2
                        for i, value in enumerate(values):
                            with nested_cols[0] if i < half_len else nested_cols[1]:
                                default_selected = value in filtered_tools[filtered_tools['risk'].isin(selected_challenges)][col].unique()
                                if st.checkbox(f"{value}", key=f'{col}_{value}', value=default_selected):
                                    selected_tools[col].append(value)
                                    stored_values.append(f"{col}{value}")

                # Introduce Forbidden Nodes selection
                st.markdown("<h2 style='text-align: center;'>Step 2/3: Select forbiden tools </h2>", unsafe_allow_html=True)
                unique_sources = matrix_df['source'].unique()
                forbidden_nodes = st.multiselect("Forbidden Tools", options=unique_sources, key='forbidden_nodes', help="Select nodes to exclude from the path")

                if st.button("Analyze", key='analyze_button'):
                    st.session_state['analyze_challenges_clicked'] = True
                    st.session_state['submit_clicked'] = False  # Reset submit_clicked state

                if st.session_state.get('analyze_challenges_clicked', False) and not st.session_state.get('submit_clicked', False):
                    st.markdown("<h2 style='text-align: center;'>Step 3/3: Select tools by Inovation Phase</h2>", unsafe_allow_html=True)
                    # Identify unique source values for matching source filter values
                    st.write("Selected Tools:")
                    unique_source_values = set()
                    for stored_value in stored_values:
                        matched_sources = matrix_df[matrix_df['source filter'] == stored_value]['source'].unique()
                        unique_source_values.update(matched_sources)
                    st.write(unique_source_values)

                    # Display checklists for each innovation group after clicking "Analyze"
                    innovation_groups = innovation_df[innovation_df['source'].isin(unique_source_values)].groupby('innovation')['source'].apply(list).to_dict()
                    grid_cols = st.columns(4)
                    innovation_order = ['Research', 'Funding', 'Engineering', 'Marketing']  # Define the order of innovation categories
                    selected_innovation_nodes = set()
                    for index, innovation in enumerate(innovation_order):
                        with grid_cols[index]:
                            st.markdown(f"#### {innovation}")
                            st.markdown("<hr>", unsafe_allow_html=True)
                            nodes = innovation_groups.get(innovation, [])
                            for node in nodes:
                                if st.checkbox(f"{node}", key=f'{innovation}_{node}', value=node in unique_source_values):
                                    selected_innovation_nodes.add(node)
                                else:
                                    selected_innovation_nodes.discard(node)

                    if st.button("Submit", key='submit_button'):
                        st.session_state['submit_clicked'] = True
                        st.session_state['selected_innovation_nodes'] = selected_innovation_nodes

                if st.session_state.get('submit_clicked', False):
                    # Proceed with analysis using the filtered selected_innovation_nodes
                    selected_nodes = st.session_state.get('selected_innovation_nodes', set())
                    if selected_nodes:
                        st.markdown("<h2 style='text-align: center;'>Analysis Result</h2>", unsafe_allow_html=True)
                        structured_summary = f'For the "{selected_player}" companies in the semicoductor ecosystem, you have selected "{selected_cat2}". The list of selected challenges is/are: {", ".join(selected_challenges)}'
                        st.write(structured_summary)
                        G = load_network_graph(gpt_df, forbidden_nodes=forbidden_nodes)
                        path = solve_tsp_with_or_tools(G, list(selected_nodes), forbidden_nodes)
                        if path:
                            # Determine initial and intermediary nodes
                            st.session_state['path'] = path
                            initial_nodes = list(selected_nodes)
                            intermediary_nodes = [node for node in path if node not in initial_nodes]

                            # Display boxes for selected nodes, intermediary nodes, and forbidden nodes
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write("Selected Tools")
                                st.table(pd.DataFrame(initial_nodes, columns=["Nodes"]))
                            with col2:
                                st.write("Intermediary Tools")
                                st.table(pd.DataFrame(intermediary_nodes, columns=["Nodes"]))
                            with col3:
                                st.write("Forbidden Tools")
                                st.table(pd.DataFrame(forbidden_nodes, columns=["Nodes"]))

                            st.write("Shortest path connecting selected tools:")
                            st.write(" -> ".join(path))

                            # Visualize the shortest path
                            visualize_shortest_path(G, path)
                            st.markdown("<h3 style='text-align: center;'>Description of interventions & KPIs to track</h2>", unsafe_allow_html=True)
                            display_filtered_info(info_df, st.session_state['path'])

                        else:
                            st.write("No path found.")
                    else:
                        st.write("No nodes selected for analysis.")
def reset_filters():
    for key in list(st.session_state.keys()):
        if key not in ['authenticated', 'username']:
            del st.session_state[key]
    st.experimental_rerun()

# Main function where the Streamlit app is defined
def main():
    # Authentication
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False  # Initial state is not authenticated
        
        
    if not st.session_state['authenticated']:
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            if username == "SGO" and password == "123":
                st.session_state['authenticated'] = True  # Update the state to authenticated
                st.experimental_rerun()  # Rerun the app to update the UI
            else:
                st.sidebar.error("Incorrect username or password")
    else:
        col1, col2 = st.columns([0.9, 0.1])  # Adjust column widths as needed
        with col2:  # This column is narrower and intended for the Restart button
            if st.button("Restart"):
                reset_filters()
        set_custom_styles()  # Apply custom styles
        st.markdown("<h1 style='text-align: center;'>Semiconductor Ecosystem</h1>", unsafe_allow_html=True)
    
        detailed_graph_url = "https://ouestware.gitlab.io/retina/beta/#/graph/?url=https://gist.githubusercontent.com/Diffusalbladez13/1d61e9d8252fe0aefc1e9c742e434fa7/raw/ee276c2ebb604d45e2dae939b53c86da871227f6/network-da8b5aa3-6ba.gexf"
        button_html = f"""<a href="{detailed_graph_url}" target="_blank">
        <button style='color: white; background-color: #4CAF50; border: none; padding: 10px 20px;
        text-align: center; text-decoration: none; display: inline-block; font-size: 16px;
        margin: 4px 2px; cursor: pointer; border-radius: 12px;'>Click here for detailed graph</button></a>"""
        st.markdown(button_html, unsafe_allow_html=True)
    
        graph_url = "https://ouestware.gitlab.io/retina/beta/#/graph/?url=https://gist.githubusercontent.com/Diffusalbladez13/95cd418a11fefb558e2ede23915419d5/raw/817d8db0ddc4c7a13988deb5870b47d9103842bb/network-3853c799-78e.gexf"
        st.markdown(f'<iframe src="{graph_url}" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)
        st.write("Note: The network analysis shown above was used to identify different types of players and catalysts present in the semiconductor ecosystem")
        # Ensure this line matches the number of parameters in the function definition
        challenge_df, tools_df, matrix_df, gpt_df, info_df, innovation_df = load_csv_data()
    
        # Now passing the correct number of arguments to match the function's definition
        display_challenge_analysis(challenge_df, tools_df, matrix_df, gpt_df, info_df, innovation_df)
if __name__ == "__main__":
    main()
