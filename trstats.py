import os
from ast import arguments
import subprocess
import statistics
import argparse
from matplotlib import mean, median
import plotly.graph_objects as go
import jc
import pprint
import glob
import numpy as np
import shutil
import json
pp = pprint.PrettyPrinter(intdent=6)



def graph( args, dist, json_output):
    c = []
for h in np.linspace(0, 360, len(dist[0])):
    color = f'hsl({h}, 50%, 50%)'
    c.append(color)

    figure = go.Figure()
for i in range(len(dist[0])):
    y_data = dist[0][i] if len(dist[0][i]) != 0 else [0]
    name = dist[1][i]
    color = c[i]
    
    box = go.Box(y=y_data, name=name, marker_color=color)
    figure.add_trace(box)

#print(len(dist[0]) , len(dist[1]))
    figure = go.Figure(data = [go.Box(y = dist[0][i] if len(dist[0][i]) != 0 else  [0] , name = dist[1][i] , marker_color = c[i]  )  for i in range(len(dist[0]))])
    for i in range(len(dist[0])):
       figure.add_trace( go.Scatter(y= [json_output[i].get("avg")] , x=[dist[1][i]], mode = "markers" , marker_color = "Brown" ,showlegend=False) )
figure.write_image(args.GRAPH+".pdf") 
return 0


def json_file(args , json_output):
    with open(args + ".json", "w") as outfile:
        json.dump(json_output, outfile, indent=6)


#when test directory is given
def hosts(lines, direct):
    #run traceroute
    hop = 1
    for lines in lines:
        contents = lines.split( " ")
        temphold = []
        for items in contents:
            if( ((item.count(".") > 1 and item != "ms") ) or "gateway" in item):
                temp_list.append(item)
    
    i = 0
    for i in range(len(temphold) - 1):
        if direct.get(hop) is None:
            host_dict[hop] = [(temphold[i],temphold[i+1])]

        else:
            direct[hop].append(temphold[i],temphold[i+1])
        
    i=i+2
    hop=hop+1
    for i in range(1,len(lines)+1):
        if direct.get(i) is None:
            direct[i] = []
        else:
            direct[i] = list(set(host_dict[i]))
    return direct



def tracerouterun( args ):
    dest = args.TARGET
    tracerun = "mkdir -p files;traceroute"
    tracerun += dest +""

if( args.MAX_HOPS is not None):
        tracerun += " -m "+args.MAX_HOPS+" "        
tracerun = f"for i in `seq 1 {args.NUM_RUNS if args.NUM_RUNS is not None else 1}` ; do "+ arguments_for_traceroute + " > test_files/tr_run-$i.txt ; " 
if( args.RUN_DELAY is not None):
        tracerun = tracerun +" sleep " + args.RUN_DELAY +  " ; "
tracerun = tracerun +" done"


try:
        shutil.rmtree(os.getcwd()+"/files")
except FileNotFoundError:
        b = 1
traceroute = subprocess.run(tracerun , check = True , stdout=subprocess.PIPE , universal_newlines=True , shell = True)

traceroute_output = traceroute.stdout
return "files"


def traceanalysis( args ):
#run traceroute and compute a json file and a pdf by the end
    producejson = {}
    node = {}
    if(  os.path.exists(args.TEST_DIR) == False):
        print("Directory doesnt exist")
        return 0


    filename = glob.glob(f"{args.TEST_DIR}/*")
    
    filename.sort()
    for file in filename:
        with open(file) as f:
            lines = f.read()
            #print(lines)
        with open(file) as f:
            linelist = f.readlines()
            linelist = linelist[1:]
            #print(linelist)
        node = create_a_host_list(linelist,node)
        data = jc.parse('traceroute' , lines)
        # print(data)
        for hop in data['hops']:
            #print(hop.get("hop"))
            if(producejson.get(hop.get("hop")) == None):
                producejson[hop.get("hop")] = {}
                producejson[hop.get("hop")]["hop"] = hop.get("hop")
                producejson[hop.get("hop")]["probes"] = []
                producejson[hop.get("hop")]["times"] = []
                for i in hop.get("probes"):
                    producejson[hop.get("hop")]["probes"].append(i.get('ip'))
                    producejson[hop.get("hop")]["times"].append(i.get('rtt'))
            else:
                for i in hop.get("probes"):
                    producejson[hop.get("hop")]["probes"].append(i.get('ip'))
                    producejson[hop.get("hop")]["times"].append(i.get('rtt'))
            # #pp.pprint(producejson)
            # #pp.pprint(hosts)

    json_output = []
    dist = [[],[]]
    
    for key in producejson.keys():
        # #pp.pprint(producejson(key).get('times'))
        producejson.get(key)['times']= [0 if i is None else i for i in producejson.get(key).get('times') ]
        dist[0].append( producejson.get(key).get('times'))
        dist[1].append(f"hop {key}")
        diction = {}
        diction['hop'] = key
        diction['node'] = tuple(set(producejson.get(key).get('probes')))
        # final_distributions.append({})
        if( len(producejson.get(key).get('times')) != 0):
            diction['avg']= mean(producejson.get(key).get('times'))
            diction['min'] = min(producejson.get(key).get('times'))
            diction['med'] = median(producejson.get(key).get('times'))
            diction['max'] = max(producejson.get(key).get('times'))
        else:
            diction['avg'] = 0
            diction['min'] = 0
            diction['med'] = 0
            diction['max'] = 0
        json_output.append(
            diction
        )

    # #pp.pprint(final_json)
    
    # #pp.pprint(dist)
    #pp.pprint(hosts)
    for i in node.keys():
        json_output[i-1]['node'] = node.get(i)
    json_file(args,json_output)
    graph(args , dist , json_output)
    pp.pprint(json_output)
    #pp.pprint(dist)
    #pp.pprint(os.getcwd())
    return 0


def compare_file_count( args ):
 
    listoffiles = glob.glob(os.getcwd()+"/test_files/*.txt")
    print(listoffiles)
    if( len(listoffiles) == args.NUM_RUNS):
        return False
    return True


def main():
    """Main function captures the arguments and based on their values the conditional flow exectution runs"""
    help_message ="""
    """
    cmdparse = argparse.ArgumentParser(description = help_message)

    
    
    cmdparse.add_argument("-n" , "--NUM_RUNS", help = "tracerout run counter" , required = False)
    cmdparse.add_argument("-d" , "--RUN_DELAY" , help = "Time delay between consecutive runs" , required = False)
    cmdparse.add_argument("-m" , "--MAX_HOPS" , help = "Upper limit of traceroute runs" , required = False )
    cmdparse.add_argument("-o","--OUTPUT" , help = "directory and name of output JSON file"  , required = True)
    cmdparse.add_argument("-g" , "--GRAPH" , help = "directory and name of output PDF file", required = True)
    cmdparse.add_argument("-t" , "--TARGET" , help = " Domain name or IP of destination" , required = False )
    cmdparse.add_argument("-test","--TEST_DIR" , help = "tracecroute run files directory", required = False)

 

  
    args = cmdparse.parse_args()

    #print(args)

    if( args.TEST_DIR is not None ):
        #check whether the test directory has the number of files that are equal to number of runs
        perform_analysis( args )

    else:
        args.__setattr__("TEST_DIR",tracerouterun( args ))
        perform_analysis( args )

    return 0


if __name__ == "__main__":
    main()


        

            

    