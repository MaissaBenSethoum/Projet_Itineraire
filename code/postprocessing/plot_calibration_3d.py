from matplotlib import cm
from matplotlib import pyplot as plt
import numpy as np
import cv2

# Plein de fonctions pour l'affichage 3D des résultats de la calibration

def inverse_homogeneoux_matrix(M):
    R = M[0:3, 0:3]
    T = M[0:3, 3]
    M_inv = np.identity(4)
    M_inv[0:3, 0:3] = R.T
    M_inv[0:3, 3] = -(R.T).dot(T)

    return M_inv

def transform_to_matplotlib_frame(cMo, X, inverse=False):
    M = np.identity(4)
    M[1,1] = 0
    M[1,2] = 1
    M[2,1] = -1
    M[2,2] = 0

    if inverse:
        return M.dot(inverse_homogeneoux_matrix(cMo).dot(X))
    else:
        return M.dot(cMo.dot(X))

def create_camera_model(camera_matrix, width, height, scale_focal, draw_frame_axis=False):
    fx = camera_matrix[0,0]
    fy = camera_matrix[1,1]
    focal = 2 / (fx + fy)
    f_scale = scale_focal * focal

    # draw image plane
    X_img_plane = np.ones((4,5))
    X_img_plane[0:3,0] = [-width, height, f_scale]
    X_img_plane[0:3,1] = [width, height, f_scale]
    X_img_plane[0:3,2] = [width, -height, f_scale]
    X_img_plane[0:3,3] = [-width, -height, f_scale]
    X_img_plane[0:3,4] = [-width, height, f_scale]

    ratio1 = 0.66
    ratio2 = 0.66
    width=height
    min_cam = -f_scale/2

    # draw camera
    X_center1 = np.array([[-width*ratio1, -width],
                          [height*ratio1, height],
                          [f_scale*ratio2, f_scale],
                          [1, 1]])

    X_center2 = np.array([[width*ratio1, width],
                          [height*ratio1, height],
                          [f_scale*ratio2, f_scale],
                          [1, 1]])

    X_center3 = np.array([[width*ratio1, width],
                          [-height*ratio1, -height],
                          [f_scale*ratio2, f_scale],
                          [1, 1]])

    X_center4 = np.array([[-width*ratio1, -width],
                          [-height*ratio1, -height],
                          [f_scale*ratio2, f_scale],
                          [1, 1]])

    X_center5 = np.stack([X_center1[:,0],X_center2[:,0]],axis=-1)
    X_center6 = np.stack([X_center2[:,0],X_center3[:,0]],axis=-1)
    X_center7 = np.stack([X_center3[:,0],X_center4[:,0]],axis=-1)
    X_center8 = np.stack([X_center4[:,0],X_center1[:,0]],axis=-1)

    X_center9 = np.stack([X_center5[:,0],X_center5[:,0]],axis=-1)
    X_center9[2,1] = min_cam
    X_center10 = np.stack([X_center6[:,0],X_center6[:,0]],axis=-1)
    X_center10[2,1] = min_cam 
    X_center11 = np.stack([X_center7[:,0],X_center7[:,0]],axis=-1)
    X_center11[2,1] = min_cam
    X_center12 = np.stack([X_center8[:,0],X_center8[:,0]],axis=-1)
    X_center12[2,1] = min_cam

    X_center13 = X_center5.copy()
    X_center13[2,:] = min_cam
    X_center14 = X_center6.copy()
    X_center14[2,:] = min_cam
    X_center15 = X_center7.copy()
    X_center15[2,:] = min_cam
    X_center16 = X_center8.copy()
    X_center16[2,:] = min_cam

    # draw camera frame axis
    X_frame1 = np.ones((4,2))
    X_frame1[0:3,0] = [0, 0, 0]
    X_frame1[0:3,1] = [f_scale/2, 0, 0]

    X_frame2 = np.ones((4,2))
    X_frame2[0:3,0] = [0, 0, 0]
    X_frame2[0:3,1] = [0, f_scale/2, 0]

    X_frame3 = np.ones((4,2))
    X_frame3[0:3,0] = [0, 0, 0]
    X_frame3[0:3,1] = [0, 0, f_scale/2]

    if draw_frame_axis:
        return [X_img_plane, X_center1, X_center2, X_center3, X_center4,
                X_center5, X_center6, X_center7, X_center8,
                X_center9, X_center10, X_center11, X_center12,
                X_center13, X_center14, X_center15, X_center16, 
                X_frame1, X_frame2, X_frame3]
    else:
        return [X_img_plane, X_center1, X_center2, X_center3, X_center4,
                X_center5, X_center6, X_center7, X_center8,
                X_center9, X_center10, X_center11, X_center12]

def create_board_model(board_width, board_height, square_size, draw_frame_axis=False):
    width = board_width*square_size
    height = board_height*square_size

    # draw calibration board
    X_board = np.ones((4,5))
    #X_board_cam = np.ones((extrinsics.shape[0],4,5))
    X_board[0:3,0] = [0,0,0]
    X_board[0:3,1] = [width,0,0]
    X_board[0:3,2] = [width,height,0]
    X_board[0:3,3] = [0,height,0]
    X_board[0:3,4] = [0,0,0]

    # draw board frame axis
    X_frame1 = np.ones((4,2))
    X_frame1[0:3,0] = [0, 0, 0]
    X_frame1[0:3,1] = [height/2, 0, 0]

    X_frame2 = np.ones((4,2))
    X_frame2[0:3,0] = [0, 0, 0]
    X_frame2[0:3,1] = [0, height/2, 0]

    X_frame3 = np.ones((4,2))
    X_frame3[0:3,0] = [0, 0, 0]
    X_frame3[0:3,1] = [0, 0, height/2]

    if draw_frame_axis:
        return [X_board, X_frame1, X_frame2, X_frame3]
    else:
        return [X_board]

def draw_camera_boards(ax, camera_matrix, cam_width, cam_height, scale_focal,
                       extrinsics, board_width, board_height, square_size,
                       patternCentric):
    min_values = np.zeros((3,1))
    min_values = np.inf
    max_values = np.zeros((3,1))
    max_values = -np.inf

    if patternCentric:
        X_moving = create_camera_model(camera_matrix, cam_width, cam_height, scale_focal)
        X_static = create_board_model(board_width, board_height, square_size)
        static_colors = ['b' for i in range(len(X_static))]
    else:
        X_static = create_camera_model(camera_matrix, cam_width, cam_height, scale_focal, True)
        X_moving = create_board_model(board_width, board_height, square_size)
        static_colors = ['b' for i in range(len(X_static))]
        static_colors[-3]='k'
        static_colors[-2]='k'
        static_colors[-1]='k'
    cm_subsection = np.linspace(0.0, 1.0, extrinsics.shape[0])
    colors = [ cm.jet(x) for x in cm_subsection]

    
    for i in range(len(X_static)):
        X = np.zeros(X_static[i].shape)
        for j in range(X_static[i].shape[1]):
            X[:,j] = transform_to_matplotlib_frame(np.eye(4), X_static[i][:,j])
        ax.plot3D(X[0,:], X[1,:], X[2,:], color=static_colors[i])
        min_values = np.minimum(min_values, X[0:3,:].min(1))
        max_values = np.maximum(max_values, X[0:3,:].max(1))

    for idx in range(extrinsics.shape[0]):
        R, _ = cv2.Rodrigues(extrinsics[idx,0:3])
        cMo = np.eye(4,4)
        cMo[0:3,0:3] = R
        cMo[0:3,3] = extrinsics[idx,3:6]
        for i in range(len(X_moving)):
            X = np.zeros(X_moving[i].shape)
            for j in range(X_moving[i].shape[1]):
                X[0:4,j] = transform_to_matplotlib_frame(cMo, X_moving[i][0:4,j], patternCentric)
            ax.plot3D(X[0,:], X[1,:], X[2,:], color=colors[idx])
            min_values = np.minimum(min_values, X[0:3,:].min(1))
            max_values = np.maximum(max_values, X[0:3,:].max(1))

    return min_values, max_values

def calibration_figure(dim_grid, # Dimensions de la grille (tuple (h,w))
                       square_size, # Taille des carreaux (en mm)
                       intrinsics, # Matrice des paramètres intrinsèques, de taille 3x3
                       rotations, # Liste des matrices de rotations de taille (3,1). La liste est de taille N (nombre d'images/échiquiers à afficher).
                       translations, # Liste des matrices de translations de taille (3,1). La liste est de taille N (nombre d'images/échiquiers à afficher).
                       indices_boards=None):
    
    board_width,board_height=dim_grid
    extrinsics = np.stack([np.concatenate([a[:,0],b[:,0]]) for a,b in zip(rotations,translations)],axis=-1).T

    if indices_boards is not None:
        extrinsics = extrinsics[indices_boards]

    fig = plt.figure()
    ax = fig.add_subplot(projection = '3d')
    ax.set_aspect("equal")

    cam_width = 32 
    cam_height = 24 
    scale_focal = 80000
    min_values, max_values = draw_camera_boards(ax, intrinsics, cam_width, cam_height,
                                                scale_focal, extrinsics, board_width,
                                                board_height, square_size, False)

    X_min,Y_min,Z_min = min_values
    X_max,Y_max,Z_max = max_values
    max_range = np.array([X_max-X_min, Y_max-Y_min, Z_max-Z_min]).max() / 2.0

    mid_x = (X_max+X_min) * 0.5
    mid_y = (Y_max+Y_min) * 0.5
    mid_z = (Z_max+Z_min) * 0.5
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)
    ax.set_xlabel('x')
    ax.set_ylabel('z')
    ax.set_zlabel('-y')
    ax.set_title('Extrinsic Parameters Visualization')
    plt.show()
