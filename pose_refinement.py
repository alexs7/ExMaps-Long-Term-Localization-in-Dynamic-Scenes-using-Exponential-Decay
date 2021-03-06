from __future__ import print_function
import urllib.request
import bz2
import os
import numpy as np
from scipy.sparse import lil_matrix
import time
from scipy.optimize import least_squares
from database import COLMAPDatabase
from parameters import Parameters
from query_image import get_all_images_names_from_db
from scipy.spatial.transform import Rotation as R

K = np.loadtxt(Parameters.query_images_camera_intrinsics)

def project(K, pose, points_3d):
    rot_m = R.from_rotvec(pose[0:3]).as_dcm()
    t = pose[3:6]
    Rt = np.r_[np.c_[rot_m,t], np.array([0,0,0,1]).reshape(1,4)]
    points_3d = np.hstack((points_3d, np.ones((points_3d.shape[0], 1))))  # make homogeneous
    points_proj = K.dot(Rt.dot(points_3d.transpose())[0:3])
    points_proj = points_proj / points_proj[2]  # divide by last coordinate
    points_proj = points_proj.transpose()
    return points_proj[:,0:2]

def f0(pose, K, points_2d, points_3d):
    # returns residuals
    points_proj = project(K, pose, points_3d)
    return (points_proj - points_2d).ravel()

def pose_refinement(image_pose, image_matches):
    points_2d = image_matches[:,0:2]
    points_3d = image_matches[:,2:5]
    rot = image_pose[0:3,0:3]
    rot_vec = R.from_dcm(rot).as_rotvec()
    t = image_pose[0:3,3]
    x0 = np.hstack((rot_vec, t))
    # TODO: Review maths here
    res = least_squares(f0, x0, verbose=0, method='lm', args=(K, points_2d, points_3d))
    pose_refined = res.x
    rot_m = R.from_rotvec(pose_refined[0:3]).as_dcm()
    t = pose_refined[3:6]
    Rt = np.r_[np.c_[rot_m, t], np.array([0, 0, 0, 1]).reshape(1, 4)]
    return Rt

def refine_poses(poses, matches):
    images_names = list(poses.keys())
    refined_poses = {}
    for name in images_names:
        image_pose = poses[name]
        image_matches = matches[name]
        refined_pose = pose_refinement(image_pose, image_matches)
        refined_poses[name] = refined_pose
    return refined_poses


#    TODO: Review and delete
# db_query = COLMAPDatabase.connect(Parameters.query_db_path)
# query_images_names = get_all_images_names_from_db(db_query)
# matches_save_path = "/Users/alex/Projects/EngDLocalProjects/LEGO/fullpipeline/colmap_data/data/feature_matching/1k/matches.npy"
# ransac_path_poses = "/Users/alex/Projects/EngDLocalProjects/LEGO/fullpipeline/colmap_data/data/RANSAC_results/1k/ransac_images_pose_0.5.npy"
# matches = np.load(matches_save_path)
# poses = np.load(ransac_path_poses)
#
# image_name = query_images_names[1]
# matches_for_image = matches.item()[image_name]
# pose_for_image = poses.item()[image_name]
# pose_refinement(matches_for_image, pose_for_image)