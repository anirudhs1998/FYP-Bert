from sklearn.cluster import KMeans
from typing import List
import numpy as np
from numpy import ndarray

def get_wcss_bcss(features, ratio: float = 0.3):
    """
    Retrieves wcss and bcss
    """

    k = 1 if ratio * len(features) < 1 else int(len(features) * ratio)
    model = get_model(k).fit(features)   
    centroids = get_centroids(model)          
    avg_wcss, wcss_per_cluster = avg_within_cluster_ss(centroids,k,model,features)
    bcss_distance = between_cluster_ss(centroids)
    cluster_args = find_closest_args(centroids, features, wcss_per_cluster)  
    return avg_wcss, bcss_distance

def cluster_features(features, ratio: float = 0.3) -> List[int]:
    """
    Clusters sentences based on the ratio
    :param ratio: Number of Clusters
    :return: Sentences index that qualify for summary
    """

    k = 1 if ratio * len(features) < 1 else int(len(features) * ratio)
    model = get_model(k).fit(features)   
    centroids = get_centroids(model)
    print("#########################")
    print("Centroids: ")
    print(centroids)
    avg_wcss, wcss_per_cluster = avg_within_cluster_ss(centroids,k,model,features)   
    print("#########################")
    print("WCSS: ")  
    print(wcss_per_cluster)
    cluster_args = find_closest_args(centroids, features, wcss_per_cluster) 
    print(cluster_args) 
    sorted_values = sorted(cluster_args.values())
    return sorted_values

def get_model(k: int):
    """
    Retrieve clustering model
    :param k: amount of clusters
    :return: Clustering model
    """
    return KMeans(n_clusters=k, random_state=12345)
    
def get_labels(model):
    """
    Retrieve labels of points
    :param model: Clustering model
    :return: Labels
    """
    return model.labels_

def get_centroids(model):
    """
    Retrieve centroids of model
    :param model: Clustering model
    :return: Centroids
    """
    return model.cluster_centers_

def find_closest_args(centroids: np.ndarray, features, wcss_per_cluster):
    """
    Find the closest arguments to centroid
    :param centroids: Centroids to find closest
    :return: Closest arguments
    """
    no_sentence_to_choose = 0
    centroid_min = 1e10
    cur_arg = -1
    args = {}
    used_idx = []
    k = 0

    for j, centroid in enumerate(centroids):

        if wcss_per_cluster[j] < 2:
            no_sentence_to_choose = 0
        elif wcss_per_cluster[j] >= 2 and wcss_per_cluster[j] < 3.85:
            no_sentence_to_choose = 1
        elif wcss_per_cluster[j] >= 3.85 and wcss_per_cluster[j] < 5.78:
            no_sentence_to_choose = 2
        else:
            no_sentence_to_choose = 3
        while no_sentence_to_choose > 0:
            for i, feature in enumerate(features):
                value = np.linalg.norm(feature - centroid)

                if value < centroid_min and i not in used_idx:
                    cur_arg = i
                    centroid_min = value

            used_idx.append(cur_arg)
            args[k] = cur_arg
            k = k + 1
            centroid_min = 1e10
            cur_arg = -1
            no_sentence_to_choose = no_sentence_to_choose - 1

    return args

def avg_within_cluster_ss(centroids:np.ndarray,k,model,features):
    """
    Find the WCSS
    :param centroids: Centroids of the each cluster
    :return: WCSS of the cluster
    """
    cluster = {i: np.where(model.labels_ == i)[0] for i in range(k)}  #Each cluster and indices in that cluster
    
    for i in range(len(cluster)):
        cluster2 = []
        for point in cluster[i]:
            cluster2.append(features[point])
            cluster[i] = cluster2      
    '''
    cluster[i] has list of points which have centroid as i     
    (cluster[0][i] - centroid[0]) distance
    '''    
    wcss = []
    wcss_total_cluster = 0
    for j,centroid in enumerate(centroids):
        centroid_dist = 0  #Sum of euclidean distances of points in each cluster
        for point in cluster[j]:
            distance = np.linalg.norm(point - centroid, 2)
            centroid_dist = centroid_dist + distance
        wcss_total_cluster = wcss_total_cluster +  centroid_dist/len(cluster[j])
        wcss.append(centroid_dist/len(cluster[j]))
    avg_wcss = wcss_total_cluster/len(centroids)
    
    return avg_wcss, wcss

def between_cluster_ss(centroids:np.ndarray):
    """
    Find the BCSS
    :param: centroids: Centroids of each cluster
    :return: BCSS of the clustering
    """
    bcss = 0
    for j,centroid in enumerate(centroids):
        current_centroid = centroid
        current_distance = 0
        for i,new_centroid in enumerate(centroids):
            distance = np.linalg.norm(current_centroid - new_centroid, 2)
            current_distance = current_distance + distance
        bcss = bcss + current_distance
       
    return bcss
            
            
            
    
