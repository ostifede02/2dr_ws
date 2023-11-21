import numpy as np
import random as rnd
import time

import os

from delta_robot import DeltaRobot
import configuration as conf


simulation = True       # if simulation == True, the set points are closer to each other for a smoother visualization
                        # if simulation == False, print data on terminal
viewer = True           # if viewr == True, can view the robot in gepetto viewer

dr = DeltaRobot(viewer)

# initialize neutral position
pos_end = conf.configuration["trajectory"]["pos_neutral"]
trajectory_routine = conf.DIRECT_TRAJECTORY_ROUTINE
state = conf.TRAJECTORY_PLANNER_STATE

# some variables for performance tracking
if not simulation:
    max_computation_elapsed_time = 0
    max_delta_t = 0

    max_delay_per_step_1 = 0
    min_delay_per_step_1 = 9999999

    max_delay_per_step_2 = 0
    min_delay_per_step_2 = 9999999


while True:
    time_start = time.time()

    # *****   READ CAMERA   *****
    if state == conf.READ_CAM_STATE:
        #
        # ...read camera position prediction and detect object type
        #

        pos_end = np.array([rnd.randint(-100, 100), 0, -260])
        t_total = 1.5 + 0.2*rnd.random()
        
        # based on object type select place position, either left or right
        if rnd.random() < 0.5:
            pos_place = np.array([-190, 0, -280])
        else:
            pos_place = np.array([190, 0, -280])

        trajectory_routine = conf.PICK_TRAJECTORY_ROUTINE
        state = conf.TRAJECTORY_PLANNER_STATE


    # *****   SET TRAJECTORY   *****
    if state == conf.TRAJECTORY_PLANNER_STATE:
        if trajectory_routine == conf.PICK_TRAJECTORY_ROUTINE:
            dr.trajectory_planner(trajectory_routine, pos_end, t_total)
        
        elif trajectory_routine == conf.PLACE_TRAJECTORY_ROUTINE:
            dr.trajectory_planner(trajectory_routine, pos_end)
        
        elif trajectory_routine == conf.DIRECT_TRAJECTORY_ROUTINE:
            dr.trajectory_planner(trajectory_routine, pos_end)
        
        state = conf.COMPUTE_NEXT_POS_STATE            

    
    # *****   COMPUTE NEXT POSITION   *****
    if state == conf.COMPUTE_NEXT_POS_STATE:
        pos_next = dr.get_pos_next(simulation)
        
        if pos_next is None:                               # end of path
            state = conf.TASK_PLANNER_STATE
            continue
        
        q_next_continuos = dr.get_q_next_continuos(pos_next)
        
        if dr.check_collisions(q_next_continuos):
            break

        stepper_1_steps, stepper_2_steps = dr.get_number_of_steps()
        delta_t = dr.get_delta_t()

        state = conf.DISPLAY_STATE


    # *****   SELECT TRAJECTORY ROUTINE   *****
    if state == conf.TASK_PLANNER_STATE:
        if trajectory_routine == conf.PICK_TRAJECTORY_ROUTINE:
            trajectory_routine = conf.PLACE_TRAJECTORY_ROUTINE
            pos_end = pos_place
            # time.sleep(0.2)     # simulate grab object
            state = conf.TRAJECTORY_PLANNER_STATE
        
        elif trajectory_routine == conf.PLACE_TRAJECTORY_ROUTINE:
            trajectory_routine = conf.DIRECT_TRAJECTORY_ROUTINE
            pos_end = conf.configuration["trajectory"]["pos_neutral"]
            # time.sleep(0.4)     # simulate place object
            state = conf.TRAJECTORY_PLANNER_STATE
        
        elif trajectory_routine == conf.DIRECT_TRAJECTORY_ROUTINE:
            trajectory_routine = conf.PICK_TRAJECTORY_ROUTINE
            # time.sleep(0.2)     # simulate wait cam for new cmd
            state = conf.READ_CAM_STATE

    
    time_end = time.time()
    

    # *****   DISPLAY GEPETTO VIEWER   *****
    if state ==  conf.DISPLAY_STATE:
        dr.display(q_next_continuos)
        time.sleep(delta_t)

        state = conf.COMPUTE_NEXT_POS_STATE

    
    # *********************************************************************************
    
    # print iteration values on screen

    # *********************************************************************************

  
    if not simulation:
        time.sleep(0.2)             # be able to read form terminal
        os.system('cls||clear')
        print("The system is running...\n")

        print("\t****  computation  *****")
        computation_elapsed_time = time_end-time_start
        max_computation_elapsed_time = max(max_computation_elapsed_time, computation_elapsed_time)
        print(f"max computation elapsed time: {round(max_computation_elapsed_time*1e3, 3)} in milliseconds")
        print(f"computation elapsed time: {round(computation_elapsed_time*1e3, 3)} in milliseconds\n")

        print("\t****  delta t  *****")
        max_delta_t = max(max_delta_t, delta_t)
        print(f"max delta t per cycle: {round(max_delta_t*1e3, 3)} in milliseconds")
        print(f"delta t per cycle: {round(delta_t*1e3, 3)} in milliseconds\n")

        print("\t****  steppers  *****")

        print("stepper 1")
        print(f"steps in delta t: {stepper_1_steps}")
        if stepper_1_steps != 0:
            delay_per_step_1 = abs(delta_t/(stepper_1_steps*2))
            max_delay_per_step_1 = max(max_delay_per_step_1, delay_per_step_1)
            min_delay_per_step_1 = min(min_delay_per_step_1, delay_per_step_1)

            print(f"delay per step: {round(delay_per_step_1*1e6, 1)} in microseconds")
            print(f"min delay per step: {round(min_delay_per_step_1*1e6, 1)} in microseconds")
            print(f"max delay per step: {round(max_delay_per_step_1*1e6, 1)} in microseconds\n")
        else:
            print(f"stepper 1 does not move!\n")

        print("stepper 2")
        print(f"steps in delta t: {stepper_2_steps}")
        if stepper_2_steps != 0:
            delay_per_step_2 = abs(delta_t/(stepper_2_steps*2))
            max_delay_per_step_2 = max(max_delay_per_step_2, delay_per_step_2)
            min_delay_per_step_2 = min(min_delay_per_step_2, delay_per_step_2)

            print(f"delay per step: {round(delay_per_step_2*1e6, 1)} in microseconds")
            print(f"min delay per step: {round(min_delay_per_step_2*1e6, 1)} in microseconds")
            print(f"max delay per step: {round(max_delay_per_step_2*1e6, 1)} in microseconds\n")
        else:
            print(f"stepper 1 does not move!\n")
