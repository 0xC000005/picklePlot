import os
import cudf
import cugraph
import graph_tool.all as gt
import time
import re
import pandas as pd

GRAPHML_FILE = "price_10000nodes.graphml"
CSV_FILE = "fixed_SNAP_price_10000nodes-edges.csv"
CUDF_EDGELIST = cudf.read_csv(CSV_FILE,
                              names=["source", "target"],
                              dtype=["string", "string"],
                              sep='\t')
CUGRAPH_GRAPH = cugraph.Graph()
CUGRAPH_GRAPH.from_cudf_edgelist(CUDF_EDGELIST, source='source', destination='target')
GRAPH_TOOL_GRAPH = gt.load_graph(GRAPHML_FILE)

def pos_df_to_graph(graphml, pos_df, name, resolution=1000):
    g = graphml
    # given a position dataframe pos_df with columns ['vertex', 'x', 'y'], create a vector<double> property map of
    # positions 'pos'
    pos = g.new_vertex_property("vector<double>")

    # if the vertex name is a string like n1234, convert it to integer 1234
    pos_df['vertex'] = pos_df['vertex'].apply(lambda x: int(re.sub("[^0-9]", "", x)))

    for i in range(len(pos_df)):
        pos[pos_df.iloc[i]['vertex']] = [pos_df.iloc[i]['x'], pos_df.iloc[i]['y']]
    g.vertex_properties['pos'] = pos

    gt.graph_draw(g, pos=pos, output_size=(resolution, resolution), output=name + '.png')


def cuGraph_to_pos_df(cuGraph_Graph, param0, param1, param2):
    # if param2 < 0.5:
    #     param2 = False
    # else:
    #     param2 = True

    # if param2 is not int, turn it into int
    if type(param2) is not int:
        param2 = int(param2)

    position_dff = cugraph.force_atlas2(cuGraph_Graph,
                                        scaling_ratio=param0,
                                        gravity=param1,
                                        max_iter=param2)
    return position_dff.to_pandas()


def retrieve_file_list(retrieve_directory='.', endswith='.pickle'):
    l = []
    for x in os.listdir(retrieve_directory):
        if x.endswith(endswith):
            l.append(x)
    return l


def process_pickle_files():
    # Get the list of all pickle files in the current directory
    pickle_files = retrieve_file_list(endswith='pickle')

    # Process each pickle file
    for file in pickle_files:
        # Read the DataFrame from the pickle file
        df = pd.read_pickle(file)

        # Get the parameters from the last two rows
        params_initial = df.iloc[0]['params']
        params_best = df.iloc[-1]['params']

        # Calculate the layouts
        pos_df_initial = cuGraph_to_pos_df(CUGRAPH_GRAPH, *params_initial)
        pos_df_best = cuGraph_to_pos_df(CUGRAPH_GRAPH, *params_best)

        # Plot the layouts
        pos_df_to_graph(GRAPH_TOOL_GRAPH, pos_df_initial, f'{file}_initial_layout')
        pos_df_to_graph(GRAPH_TOOL_GRAPH, pos_df_best, f'{file}_best_layout')


# Run the function
process_pickle_files()
