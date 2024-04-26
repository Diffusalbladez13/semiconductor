# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 12:40:37 2024

@author: tkannand
"""

import streamlit as st
import pandas as pd
import networkx as nx
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import matplotlib.pyplot as plt  # Import matplotlib for graph visualization

# Function to load data from CSV files
def load_csv_data():
    challenge_df = pd.read_csv("challenge.csv")
    tools_df = pd.read_csv("tool.csv")
    matrix_df = pd.read_csv("matrix.csv")
    gpt_df = pd.read_csv("gpt.csv")  # Assuming you have a gpt.csv for the graph
    return challenge_df, tools_df, matrix_df, gpt_df

# Function to load and process network graph from GPT CSV
def load_network_graph(gpt_df):
    G = nx.from_pandas_edgelist(gpt_df, 'source', 'target', create_using=nx.DiGraph())
    return G

# New TSP-based shortest path finding function using OR-Tools
def solve_tsp_with_or_tools(G, selected_nodes):
    # Ensure selected_nodes are actually in G
    selected_nodes = [node for node in selected_nodes if node in G]

    node_to_index = {node: i for i, node in enumerate(selected_nodes)}
    index_to_node = {i: node for node, i in node_to_index.items()}

    num_nodes = len(selected_nodes)
    distance_matrix = [[0 if i == j else nx.shortest_path_length(G, source=selected_nodes[i], target=selected_nodes[j], weight='weight', method='dijkstra')
                        for j in range(num_nodes)] for i in range(num_nodes)]

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
        return None

# Function to visualize the shortest path
# Updated Function to visualize the shortest path with improvements for neatness
def visualize_shortest_path(G, path):
    # Use Kamada-Kawai layout for better node distribution in complex graphs
    pos = nx.kamada_kawai_layout(G)
    plt.figure(figsize=(12, 8))
    
    # Draw the full graph with lighter and thinner edges and smaller nodes
    # Only draw nodes and edges without labels
    nx.draw(G, pos, with_labels=False, node_color='lightblue', edge_color='gray', width=0.5, node_size=200, alpha=0.6)
    
    # Highlight the path in the graph
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_nodes(G, pos, nodelist=path, node_color='red', node_size=250)
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='red', width=2, alpha=0.9)
    
    # Draw labels only for the nodes in the path
    path_labels = {n: n for n in path}
    nx.draw_networkx_labels(G, pos, labels=path_labels, font_color='black')
    
    plt.title("Shortest Path Visualization")
    plt.axis('off')  # Turn off the axis for a cleaner look
    st.pyplot(plt)  # Display the plot in Streamlit


# Function to display challenge analysis options and corresponding tools
def display_challenge_analysis(challenge_df, tools_df, matrix_df, gpt_df):
    player_options = ['All'] + list(challenge_df['player'].unique())
    selected_player = st.selectbox("Player", options=player_options, index=0, key='selected_player')

    cat2_options = ['All'] + list(challenge_df['cat 2'].unique())
    selected_cat2 = st.selectbox("Cat 2", options=cat2_options, index=0, key='selected_cat2')

    if selected_player != 'All' or selected_cat2 != 'All':
        if selected_player != 'All':
            challenge_df = challenge_df[challenge_df['player'] == selected_player]
        if selected_cat2 != 'All':
            challenge_df = challenge_df[challenge_df['cat 2'] == selected_cat2]

        st.write("Select Challenges:")
        challenges = challenge_df['challenge'].unique()
        selected_challenges = []
        for challenge in challenges:
            if st.checkbox(challenge, key=f'checkbox_{challenge}'):
                selected_challenges.append(challenge)

        if selected_challenges:
            st.write("Tools for Selected Challenges:")
            filtered_tools = tools_df
            cols = ['Consumers of semiconductors', 'Education and Research Institutions', 'Financial & Legal', 'Government & Regulators', 'Industry Associations and Alliances', 'Semiconductor manufacturing']
            selected_tools = {col: [] for col in cols}
            stored_values = []

            max_tools = max(len(filtered_tools[col].dropna().unique()) for col in cols)

            grid_cols = st.columns(3)
            for index, col in enumerate(cols):
                with grid_cols[index % 3]:
                    st.markdown(f"#### {col}")
                    st.markdown("<hr>", unsafe_allow_html=True)
                    values = filtered_tools[col].dropna().unique()
                    for _ in range(max_tools):
                        if _ < len(values):
                            value = values[_]
                            default_selected = value in filtered_tools[filtered_tools['risk'].isin(selected_challenges)][col].unique()
                            if st.checkbox(f"{value}", key=f'{col}_{value}_{_}', value=default_selected):
                                selected_tools[col].append(value)
                                stored_values.append(f"{col}{value}")
                        else:
                            st.empty()

            if st.button("Analyze"):
                st.write("Selected Challenges and Tools:")
                selected_data = {"Challenges": selected_challenges}
                selected_data.update({col: selected_tools[col] for col in cols})
                st.table(pd.DataFrame(dict([(k, pd.Series(v)) for k, v in selected_data.items()])))

                # Display unique source values for matching source filter values
                st.write("Unique Source Values for Matching Source Filter Values:")
                unique_source_values = set()
                for stored_value in stored_values:
                    matched_sources = matrix_df[matrix_df['source filter'] == stored_value]['source'].unique()
                    unique_source_values.update(matched_sources)

                # Display as comma-separated list
                if unique_source_values:
                    st.write(", ".join(unique_source_values))
                else:
                    st.write("No unique source values found for the stored values.")

                # Display structured selection summary
                structured_summary = f'For the "{selected_player}" player, the "{selected_cat2}" category 2 are {", ".join(selected_challenges)}.'
                st.write(structured_summary)
                unique_source_values = set()
                for stored_value in stored_values:
                    matched_sources = matrix_df[matrix_df['source filter'] == stored_value]['source'].unique()
                    unique_source_values.update(matched_sources)

                if unique_source_values:
                    G = load_network_graph(gpt_df)
                    path = solve_tsp_with_or_tools(G, list(unique_source_values))
                    if path:
                        # Determine initial and intermediary nodes
                        initial_nodes = list(unique_source_values)
                        intermediary_nodes = [node for node in path if node not in initial_nodes]

                        st.write("TSP-based Shortest Path:")
                        st.write(" -> ".join(path))

                        # Checkboxes for selecting initial and intermediary nodes
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("Initial Nodes:")
                            for index, node in enumerate(initial_nodes):
                                st.checkbox(node, key=f'init_{index}_{node}', value=True)
                        with col2:
                            st.write("Intermediary Nodes:")
                            for index, node in enumerate(intermediary_nodes):
                                st.checkbox(node, key=f'inter_{index}_{node}', value=True)

                        # Visualize the shortest path
                        visualize_shortest_path(G, path)
                    else:
                        st.write("No path found.")
                else:
                    st.write("No unique source values found for the stored values.")

# Main function where the Streamlit app is defined
def main():
    st.set_page_config(layout="wide")
    st.markdown("<h1 style='text-align: center;'>Embedded Graph in Streamlit</h1>", unsafe_allow_html=True)

    detailed_graph_url = "https://ouestware.gitlab.io/retina/beta/#/graph/?url=https%3A%2F%2Fgist.githubusercontent.com%2FDiffusalbladez13%2F95624373e22ba0cbf9eda3660772eebc%2Fraw%2F92907a8fc8fe9ea248cb37c4d13c6ef1d4c1f65f%2Fnetwork-9b01f649-aab.gexf"
    button_html = f"""<a href="{detailed_graph_url}" target="_blank">
    <button style='color: white; background-color: #4CAF50; border: none; padding: 10px 20px;
    text-align: center; text-decoration: none; display: inline-block; font-size: 16px;
    margin: 4px 2px; cursor: pointer; border-radius: 12px;'>Click here for detailed graph</button></a>"""
    st.markdown(button_html, unsafe_allow_html=True)

    graph_url = "https://ouestware.gitlab.io/retina/beta/#/graph/?url=https://gist.githubusercontent.com/Diffusalbladez13/5d5b8f2593120f01f9777b6421c1c117/raw/d122abbfa929be4273d4bc84431479210cbe7071/network-d00f20a4-22d.gexf"
    st.markdown(f'<iframe src="{graph_url}" width="100%" height="600" frameborder="0"></iframe>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Analyze challenges", key="analyze"):
            st.session_state['analyze_challenges_clicked'] = True

    if st.session_state.get('analyze_challenges_clicked', False):
        challenge_df, tools_df, matrix_df, gpt_df = load_csv_data()
        display_challenge_analysis(challenge_df, tools_df, matrix_df, gpt_df)

if __name__ == "__main__":
    main()
