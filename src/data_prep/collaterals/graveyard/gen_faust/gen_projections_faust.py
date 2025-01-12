"""
Generate projections
usage:
cd into pyRender/src
then run:
python gen_projections.py ./../resources/human.off --output_path='./projections/' --output='mask'
if you want to save the pointclouds for visualization, use --output='ply'
"""

# pyrender can be found at: https://github.com/hjwdzh/pyRender

import numpy as np
import sys
import skimage.io as sio
import os
import sys
import shutil
from objloader import LoadTextureOBJ
import time
import gc

libpath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(libpath + '/../lib')
import render
import objloader
# import pc_utils
# from pc_utils import write_ply
import pdb
import argparse
import plyfile

# input_obj = sys.argv[1]

# parser = argparse.ArgumentParser()
# parser.add_argument('--output_path', default='./data/', help='[ply, mask]')
# parser.add_argument('--output', default='ply', help='[ply, mask]')
# parser.add_argument('--num_ang',type=int, default=10, help='')
# parser.add_argument('--filename',default='./../resources/human.off', help='')

# args = parser.parse_args()


# f = open("file_list.txt", "r")
# files = [line.strip("\n") for line in f]
# f.close()


path = os.path.join(os.getcwd(), os.pardir, "data", "faust")
files = os.listdir(path)
i = 0

for file in files:

    if file.endswith(".ply"):

        t = time.time()

        ply_file = plyfile.PlyData.read(os.path.join(path, file))

        V_ply = ply_file["vertex"]
        V = np.zeros((6890, 3))
        V[:, 0] = V_ply["x"]
        V[:, 1] = V_ply["y"]
        V[:, 2] = V_ply["z"]

        V = V * 50

        F_ply = ply_file["face"].data["vertex_indices"]
        F_ply_lst = list(F_ply)
        F = np.zeros((F_ply.shape[0], 3))
        for i in range(len(F_ply_lst)):
            F[i, :] = F_ply_lst[i]

        print(V.shape, F.shape)
        print(np.min(V), np.max(V))
        print(V)
        print(F)

        # if args.filename[-3:] == 'obj':
        #	V, F, VT, FT, VN, FN, face_mat, kdmap = objloader.LoadTextureOBJ(input_obj)
        # else:
        #	V, F = objloader.LoadOff(args.filename)
        #
        # print(np.min(V), np.max(V))

        # set up camera information',
        info = {'Height': 480, 'Width': 640, 'fx': 575, 'fy': 575, 'cx': 319.5, 'cy': 239.5}
        render.setup(info)

        # set up mesh buffers in cuda
        context = render.SetMesh(V, F)

        cam2world = np.array([[0.85408425, 0.31617427, -0.375678, 0.56351697 * 2],
                              [0., -0.72227067, -0.60786998, 0.91180497 * 2],
                              [-0.52013469, 0.51917219, -0.61688, 0.92532003 * 2],
                              [0., 0., 0., 1.]], dtype=np.float32)

        # rotate the mesh elevation by 30 degrees
        Rx = np.array([[1, 0, 0, 0],
                       [0., np.cos(np.pi / 6), -np.sin(np.pi / 6), 0],
                       [0, np.sin(np.pi / 6), np.cos(np.pi / 6), 0],
                       [0., 0., 0., 1.]], dtype=np.float32)

        cam2world = np.matmul(Rx, cam2world)

        # rotate along y axis and render
        for i_ang, ang in enumerate(np.linspace(0, 2 * np.pi, 10)):

            Ry = np.array([[np.cos(ang), 0, -np.sin(ang), 0],
                           [0., 1, 0, 0],
                           [np.sin(ang), 0, np.cos(ang), 0],
                           [0., 0., 0., 1.]], dtype=np.float32)

            world2cam = np.linalg.inv(np.matmul(Ry, cam2world)).astype('float32')

            # the actual rendering process
            render.render(context, world2cam)

            # get depth information
            depth = render.getDepth(info)

            # get information of mesh rendering
            # vindices represents 3 vertices related to pixels
            # vweights represents barycentric weights of the 3 vertices
            # findices represents the triangle index related to pixels
            vindices, vweights, findices = render.getVMap(context, info)
            mask = np.unique(vindices)
            if len(mask) == 1:
                print(file)

            output_path = os.path.join(os.getcwd(), "data_output_faust")
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            out_name = file[:-4] + "_" + str(i_ang)
            np.savez(os.path.join(output_path, out_name), mask=mask)

        render.Clear()
        gc.collect()

        print(f"time: {time.time() - t}")
