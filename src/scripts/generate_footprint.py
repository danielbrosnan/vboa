"""
Concept proof for generating the footprint of a satellite using
the aperture angle of the instrument and the attitude of the
satellite (roll, pitch and yaw)

Written by DEIMOS Space S.L. (dibb)

module vboa

Install the following packages to use this module:
pip3 install numpy
pip3 install matplotlib
pip3 install astropy
pip3 install lxml
pip3 install scipy

For obtaining the desired output to be inserted in a POLYGON for BOA, execute the script as follows:
python3 generate_footprint.py -s 6835.1440 -a 0.705176738839256 -r 45 -p 45 -y 0 -e "2022-07-09T10:37:10" -i 300 -x "[-296.21575306040904, 4140.855703498794, 5432.194461466122, 51.132758229891624, 5685.677125894183, 3793.9918086159965, 392.77759064601094, 6598.242940775101, 1732.8505917276358, 690.6225570113636, 6775.21422817452, -521.91994838315167, 911.3418738829949, 6195.610155822812, -2718.2012027520733]" -d

"""
# Import python utilities
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
import math
from dateutil import parser
import datetime
import traceback
import sys

# Import xml parser
from lxml import etree

# Import astropy utilities
from astropy.coordinates import SkyCoord, ITRS
from astropy.time import Time

# Import scipy utilities
from scipy.spatial.transform import Rotation as R

##########
# Configurations
##########
# Set the radius of the Earth in km
earth_radius = 6378.1370
# Set the orbit of the satellite in km
semimajor = earth_radius

def define_rotation_axis(axis, degrees):
    '''
    Function to define the rotation axis given the axis and the degrees to rotate

    :param axis: List of X, Y and Z values
    :type axis: list
    :param degrees: degrees to rotate
    :type degrees: float

    :return: rotation to apply
    :rtype: rotation
    '''

    rotation_vector = np.radians(degrees) * np.array(axis)

    return R.from_rotvec(rotation_vector)

def plot_vector(ax, x, y, z, color = "C1", label = None):
    '''
    Function to plot the received vector in the received figure with the specified color and label

    :param ax: axes of the figure
    :type ax: plt.axes
    :param x: X position of the vector
    :type x: float
    :param y: Y position of the vector
    :type y: float
    :param z: Z position of the vector
    :type z: float
    :param color: Color to associate to the vector
    :type color: str
    :param label: Label to associate to the vector
    :type label: str
    '''
    soa = np.array([[0, 0, 0, x, y, z]])
    X, Y, Z, U, V, W = zip(*soa)
    ax.quiver(X, Y, Z, U, V, W, color=color, arrow_length_ratio = 0.03, label=label)

def display_satellite_footprint(satellite_positions, alpha, roll, pitch, yaw, ax = None):
    '''
    Function to display the satellite footprint

    :param satellite_positions: list of satellite positions [x1, y1, z1, ..., xn, yn, zn]
    :type satellite_positions: list
    :param alpha: aperture angle of the instrument
    :type alpha: float
    :param roll: roll angle of the attitude of the satellite
    :type roll: float
    :param pitch: pitch angle of the attitude of the satellite
    :type pitch: float
    :param yaw: yaw angle of the attitude of the satellite
    :type yaw: float
    :param ax: axes of the figure
    :type ax: plt.axes

    :return: axes of the figure
    :rtype: plt.axes
    '''

    print("Genearing footprint with the following configuration:\n\t- semimajor: {}\n\t- alpha: {}\n\t- roll: {}\n\t- pitch: {}\n\t- yaw: {}\n".format(semimajor, alpha, roll, pitch, yaw))
    
    create_figure = False
    # Creating an empty figure or plot
    if not ax:
        create_figure = True
        fig = plt.figure()

        # Defining the axes as a 3D axes so that we can plot 3D data into it.
        ax = plt.axes(projection="3d")

        # Set title
        ax.set_title("Satellite footprint")
    # end if

    # Set axis limits
    ax.set_xlim([-7000, 7000])
    ax.set_ylim([-7000, 7000])
    ax.set_zlim([-7000, 7000])

    # Calculate angles corresponding to the effect of the pitch
    if pitch != 0:
        pitch_radians = (pitch*2*math.pi)/360
        pitch_a_radians = math.asin(((semimajor)*math.sin(pitch_radians))/earth_radius)
        pitch_a_degrees = 180-(pitch_a_radians*360)/(2*math.pi)
        pitch_b_degrees = 180-pitch_a_degrees-pitch
        pitch_b_radians = (pitch_b_degrees*2*math.pi)/360
        print("\n###Angles for pitch###")
        print("a angle in degrees: {}".format(pitch_a_degrees))
        print("b angle in degrees: {}".format(pitch_b_degrees))
    # end if

    # Calculate angles corresponding to the aperture of the instrument seen from ground (using roll + alpha)
    alpha_radians = (alpha*2*math.pi)/360
    roll_radians = (roll*2*math.pi)/360
    roll_a1_radians = math.asin(((semimajor)*math.sin(roll_radians-alpha_radians))/earth_radius)
    roll_a1_degrees = 180-(roll_a1_radians*360)/(2*math.pi)
    roll_a2_radians = math.asin(((semimajor)*math.sin(roll_radians))/earth_radius)
    roll_a2_degrees = 180-(roll_a2_radians*360)/(2*math.pi)
    roll_a3_radians = math.asin(((semimajor)*math.sin(roll_radians+alpha_radians))/earth_radius)
    roll_a3_degrees = 180-(roll_a3_radians*360)/(2*math.pi)
    roll_b1 = 180-roll_a1_degrees-roll+alpha
    roll_b2 = 180-roll_a2_degrees-roll
    roll_b3 = 180-roll_a3_degrees-roll-alpha
    
    print("\n###Angles for roll###")
    print("a angles in radians -> a1: {}, a2: {}, a3: {}".format(roll_a1_radians, roll_a2_radians, roll_a3_radians))
    print("a angles in degrees -> a1: {}, a2: {}, a3: {}".format(roll_a1_degrees, roll_a2_degrees, roll_a3_degrees))
    print("Aperture angles from ground -> b1: {}, b2: {}, b3: {}".format(roll_b1, roll_b2, roll_b3))
    
    x_satellite_line = []
    y_satellite_line = []
    z_satellite_line = []
    x_satellite_projection_line = []
    y_satellite_projection_line = []
    z_satellite_projection_line = []
    x_left_line = []
    y_left_line = []
    z_left_line = []
    x_right_line = []
    y_right_line = []
    z_right_line = []
    i = 0
    satellite_coordinates = []
    right_coordinates = []
    left_coordinates = []
    while i < len(satellite_positions):
        # Get X, Y and Z position of the satellite
        satellite_x = satellite_positions[i]
        satellite_y = satellite_positions[i+1]
        satellite_z = satellite_positions[i+2]

        plot_vector(ax, satellite_x, satellite_y, satellite_z, color = "C4")
        # Populate line to plot
        x_satellite_line.append(satellite_x)
        y_satellite_line.append(satellite_y)
        z_satellite_line.append(satellite_z)


        satellite_position = SkyCoord(x=satellite_x, y=satellite_y, z=satellite_z, frame='itrs', unit=("km", "km", "km"), representation_type="cartesian")
        latitude = satellite_position.earth_location.lat.value
        longitude = satellite_position.earth_location.lon.value
        satellite_projection = SkyCoord(lat=latitude, lon=longitude, distance=earth_radius, frame='itrs', unit=("deg", "deg", "km"), representation_type="spherical")

        satellite_projection_x = satellite_projection.earth_location.x.value
        satellite_projection_y = satellite_projection.earth_location.y.value
        satellite_projection_z = satellite_projection.earth_location.z.value

        satellite_coordinates.append("{} {}".format(satellite_projection.earth_location.lon.value, satellite_projection.earth_location.lat.value))

        plot_vector(ax, satellite_projection_x, satellite_projection_y, satellite_projection_z, color = "C5", label=r'$\vec{PROJ}$')
        x_satellite_projection_line.append(satellite_projection_x)
        y_satellite_projection_line.append(satellite_projection_y)
        z_satellite_projection_line.append(satellite_projection_z)

        i += 3

        # Set the positions in the array of the sibling satellite position
        x_position_sibling = i
        y_position_sibling = i+1
        z_position_sibling = i+2
        rotation_axis_sign = 1
        if i >= len(satellite_positions):
            x_position_sibling = i-6
            y_position_sibling = i-5
            z_position_sibling = i-4
            rotation_axis_sign = -1
        # end if

        # Get X, Y and Z position for the following set
        satellite_sibling_x = satellite_positions[x_position_sibling]
        satellite_sibling_y = satellite_positions[y_position_sibling]
        satellite_sibling_z = satellite_positions[z_position_sibling]

        # Get perpendicular vector to satellite positions
        axis_pitch = np.cross([satellite_x, satellite_y, satellite_z], [satellite_sibling_x, satellite_sibling_y, satellite_sibling_z])*rotation_axis_sign

        plot_vector(ax, axis_pitch[0]/10000, axis_pitch[1]/10000, axis_pitch[2]/10000, color="C6", label=r'$\vec{PITCHAXIS}$')

        # Define rotations for pitch
        if pitch != 0:
            axis_pitch_unit = axis_pitch / np.linalg.norm(axis_pitch)
            rotation_pitch_b = define_rotation_axis([axis_pitch_unit[0], axis_pitch_unit[1], axis_pitch_unit[2]], pitch_b_degrees)

            satellite_projection_pitch_b = rotation_pitch_b.apply([satellite_projection_x, satellite_projection_y, satellite_projection_z])

            axis_roll = np.cross([satellite_projection_pitch_b[0], satellite_projection_pitch_b[1], satellite_projection_pitch_b[2]], [axis_pitch[0], axis_pitch[1], axis_pitch[2]])
        else:
            satellite_projection_pitch_b = [satellite_projection_x, satellite_projection_y, satellite_projection_z]
            axis_roll = np.cross([satellite_x, satellite_y, satellite_z], [axis_pitch[0], axis_pitch[1], axis_pitch[2]])
        # end if

        plot_vector(ax, satellite_projection_pitch_b[0], satellite_projection_pitch_b[1], satellite_projection_pitch_b[2], color="C7", label=r'$\vec{PITCHB}$')
        plot_vector(ax, axis_roll[0]/10000000, axis_roll[1]/10000000, axis_roll[2]/10000000, color="C8", label=r'$\vec{ROLLAXIS}$')

        # Define rotations for roll + alpha
        axis_roll_unit = axis_roll / np.linalg.norm(axis_roll)

        rotation_roll_alpha_b1 = define_rotation_axis([axis_roll_unit[0], axis_roll_unit[1], axis_roll_unit[2]], roll_b1)
        rotation_roll_alpha_b3 = define_rotation_axis([axis_roll_unit[0], axis_roll_unit[1], axis_roll_unit[2]], roll_b3)

        satellite_projection_roll_b1 = rotation_roll_alpha_b1.apply([satellite_projection_pitch_b[0], satellite_projection_pitch_b[1], satellite_projection_pitch_b[2]])
        satellite_projection_roll_b3 = rotation_roll_alpha_b3.apply([satellite_projection_pitch_b[0], satellite_projection_pitch_b[1], satellite_projection_pitch_b[2]])

        plot_vector(ax, satellite_projection_roll_b1[0], satellite_projection_roll_b1[1], satellite_projection_roll_b1[2], color="C9", label=r'$\vec{ROLLB1}$')
        plot_vector(ax, satellite_projection_roll_b3[0], satellite_projection_roll_b3[1], satellite_projection_roll_b3[2], color="C10", label=r'$\vec{ROLLB3}$')

        # Populate lines to plot
        x_right_line.append(satellite_projection_roll_b1[0])
        y_right_line.append(satellite_projection_roll_b1[1])
        z_right_line.append(satellite_projection_roll_b1[2])

        x_left_line.append(satellite_projection_roll_b3[0])
        y_left_line.append(satellite_projection_roll_b3[1])
        z_left_line.append(satellite_projection_roll_b3[2])

        # Obtain latitude and longitudes of the footprint
        footprint_right_position = satellite_projection_roll_b1
        footprint_left_position = satellite_projection_roll_b3

        footprint_right_position = SkyCoord(x=satellite_projection_roll_b1[0], y=satellite_projection_roll_b1[1], z=satellite_projection_roll_b1[2], frame='itrs', unit=("km", "km", "km"), representation_type="cartesian")
        right_coordinates.append("{} {}".format(footprint_right_position.earth_location.lon.value, footprint_right_position.earth_location.lat.value))

        footprint_left_position = SkyCoord(x=satellite_projection_roll_b3[0], y=satellite_projection_roll_b3[1], z=satellite_projection_roll_b3[2], frame='itrs', unit=("km", "km", "km"), representation_type="cartesian")
        left_coordinates.append("{} {}".format(footprint_left_position.earth_location.lon.value, footprint_left_position.earth_location.lat.value))

        
    # end while

    if create_figure:
        ax.quiver(-3, 0, 0, 7000, 0, 0, color='C1', arrow_length_ratio=0.05, label=r'$\vec{x}$') # x-axis
        ax.quiver(0, -3, 0, 0, 7000, 0, color='C2', arrow_length_ratio=0.05, label=r'$\vec{y}$') # y-axis
        ax.quiver(0, 0, -3, 0, 0, 7000, color='C3', arrow_length_ratio=0.1, label=r'$\vec{z}$') # z-axis
    # end if

    plt.legend()
    ax.plot(x_satellite_line, y_satellite_line, z_satellite_line)
    ax.plot(x_satellite_projection_line, y_satellite_projection_line, z_satellite_projection_line)
    ax.plot(x_right_line, y_right_line, z_right_line)
    ax.plot(x_left_line, y_left_line, z_left_line)

    # Print coordinates
    satellite_coordinates_to_reverse = satellite_coordinates.copy()
    satellite_coordinates_to_reverse.reverse()
    print("\nSATELLITE COORDINATES: {}".format(", ".join(satellite_coordinates) + ", " + ", ".join(satellite_coordinates_to_reverse)))

    # Reverse left coordinates to join with right coordinates
    left_coordinates.reverse()    
    print("\nFOOTPRINT COORDINATES: {}".format(", ".join(right_coordinates) + ", " + ", ".join(left_coordinates) + ", " + right_coordinates[0]))

    return ax

def main():

    args_parser = argparse.ArgumentParser(description="Concept proof for generating the footprint of a satellite using the aperture angle of the instrument and the attitude of the satellite (roll, pitch and yaw).")
    args_parser.add_argument("-s", dest="semimajor", type=float, nargs=1,
                             help="Semimajor axis of the orbit of the satellite", required=True)
    args_parser.add_argument("-a", dest="alpha", type=float, nargs=1,
                             help="Aperture angle of the instrument", required=True)
    args_parser.add_argument("-r", dest="roll", type=float, nargs=1,
                             help="Roll angle of the attitude of the satellite", required=True)
    args_parser.add_argument("-p", dest="pitch", type=float, nargs=1,
                             help="Pitch angle of the attitude of the satellite", required=True)
    args_parser.add_argument("-y", dest="yaw", type=float, nargs=1,
                             help="Yaw angle of the attitude of the satellite", required=True)
    args_parser.add_argument("-i", dest="interval", type=float, nargs=1,
                             help="Interval of time between satellite positions", required=True)
    args_parser.add_argument("-e", dest="epoch", type=str, nargs=1,
                             help="Epoch associated to the first satellite position", required=True)
    args_parser.add_argument("-x", dest="satellite_positions", type=str, nargs=1,
                             help="List of satellite positions in the Earth inertial reference frame", required=True)
    args_parser.add_argument("-t", "--print_output",
                             help="Print positions of the satellite at the limits of the visibility mask of the station", action="store_true")
    args_parser.add_argument("-d", "--display_figures",
                             help="Display figures showing the transformations done to obtain the positions of the satellite at the limits of the visibility mask of the station", action="store_true")

    args = args_parser.parse_args()

    # Semimajor axis
    semimajor_input = args.semimajor[0]
    global semimajor
    semimajor = semimajor_input

    global satellite_orbit
    satellite_orbit = semimajor - earth_radius

    # Alpha
    alpha = args.alpha[0]

    # Roll
    roll = args.roll[0]

    # Pitch
    pitch = args.pitch[0]

    # Yaw
    yaw = args.yaw[0]

    #####
    # Transform satellite positions in the Earth inertial reference frame to the Earth fixed reference frame
    #####
    epoch = args.epoch[0]
    interval = args.interval[0]
    try:
        inertial_satellite_positions = eval(args.satellite_positions[0])
    except SyntaxError as e:
        print("\nERROR: The list of satellite positions should be a string with the form [X1, Y1, Z1, ..., Xn, Yn, Zn]. Exception raised while evaluating it: {}".format(e))
        traceback.print_exc(file=sys.stdout)
        exit(-1)
    # end try

    if type(inertial_satellite_positions) != list:
        print("\nERROR: The list of satellite positions should be a string with the form [X1, Y1, Z1, ..., Xn, Yn, Zn]. Received value has type: {}".format(type(inertial_satellite_positions)))
        exit(-1)
    # end if
    if len(inertial_satellite_positions) % 3 != 0:
        print("\nERROR: The list of satellite positions should be a list of groups of X, Y and Z coordinates. Received value has {} missing coordinate/s".format(3 - len(inertial_satellite_positions) % 3))
        exit(-1)
    # end if
    
    # Obtain satellite positions referenced in the Earth fixed frame
    satellite_positions = []
    i = 0
    j = 0
    while i < len(inertial_satellite_positions):
        reference_time = parser.parse(epoch) + datetime.timedelta(seconds=j*interval)
        time = Time(reference_time.isoformat(), format="isot", scale="utc")
        inertial_satellite_position = SkyCoord(x=inertial_satellite_positions[i], y=inertial_satellite_positions[i+1], z=inertial_satellite_positions[i+2], frame="teme", unit=("km", "km", "km"), representation_type="cartesian", obstime=time)
        fixed_satellite_position = inertial_satellite_position.transform_to(ITRS())

        # Store X, Y, Z values referenced in the Earth fixed frame
        satellite_positions.append(fixed_satellite_position.earth_location.x.value)
        satellite_positions.append(fixed_satellite_position.earth_location.y.value)
        satellite_positions.append(fixed_satellite_position.earth_location.z.value)
        i += 3
        j += 1
    # end while
    
    # Display footprint of the satellite
    display_satellite_footprint(satellite_positions, alpha = alpha, roll = roll, pitch = pitch, yaw = yaw)
    
    # Showing the above plot
    display_figures = args.display_figures
    if display_figures:
        plt.show()
    # end if

if __name__ == "__main__":

    main()
