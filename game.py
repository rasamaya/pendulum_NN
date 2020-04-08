import pygame
import numpy as np
from display import Menu
from model import Seq
from pop import Pop
from debug import db

class Pendulum():
    '''
    #TODO:
        1) implement board reset so pygame doesn't have to load/quit/reload...
    '''

    def __init__(self, model=None, sim=True):
        self.model = model
        self.sim = sim

        self.w = int(1500)
        self.h = int(self.w/2)

        if self.sim:
            pygame.init()
            self.win = pygame.display.set_mode((self.w,self.h))
            pygame.display.set_caption("Inverse Pendulum")
            self.font = pygame.font.SysFont(None, 24)

    def nn(self, train=False, ind=None):
        '''
        - Plays the game with a neural net player
        
        - Args
            train: If train, return the fitness score after a number of game ticks, \
                    else play forever

        Returns:
            np array of fitness scores
        '''

        # import tensorflow as tf
        # # tf.logging.set_verbosity(tf.logging.ERROR)
        # self.model = Seq()
        
        # if self.sim == False:
        #     from keras.backend.tensorflow_backend import set_session
        #     config = tf.ConfigProto()
        #     config.gpu_options.per_process_gpu_memory_fraction = 1/9
        #     set_session(tf.Session(config=config))

        self.model._set_weights(ind)

        return self.play(play=not train, nn=True)

    def play(self, play=True, nn=False, ticks=250):

        fitness = 0
        fitness_loc = (0.9*self.w, 0.05*self.h)

        ##############
        ### Colors ###
        ##############

        cb = (0, 0, 0)
        cdg = (252, 252, 252)
        clg = (70, 70, 70)

        ###########################
        ### Physical properties ###
        ###########################

        # arm length
        ra = int(self.w/10)
        # ball radii
        rb = int(self.w/100)
        # current angle
        o0 = -np.pi/2
        # angular velocity, delta theta
        do = 0
        # ball end coordinates (0: x, 1: y)
        a0 = int(self.w/2)
        a1 = int(self.h/2 - ra)
        b0 = a0 - int(ra * np.cos(o0))
        b1 = a1 - int(ra * np.sin(o0))
        # rail length and endpoints
        rdx = int(self.w/3)
        r1 = (int(self.w/2 - rdx), a1)
        r2 = (int(self.w/2 + rdx), a1)

        ################
        ### Movement ###
        ################

        # velocities
        vd = 5
        vax = 0
        dv = 0
        adv = 0.0035
        # friction due to wall (inelastic collision)
        fw = 0.45
        # friction due to rail (deceleration constant)
        fr = 2
        # friction at the join of a (fractional angular velocity retention)
        fj = 0.991
        # gravity
        g = - 4

        #################
        ### Test vars ###
        #################

        #TODO: get rid of globals
        rmin = np.sqrt( (a0 - b0)**2 + (a1 - b1)**2)
        rmax = rmin

        #################
        ### Load Menu ###
        #################

        if play:
            menu = Menu(win=self.win, 
                        w=self.w,
                        h=self.h,
                        params={'g': (g,0,-10),
                                'fr': (fr,0,10),
                                'fj': (fj, 0.8,1.1),
                                'fw': (fw, 0, 1)})


        #######################
        ### game state loop ###
        #######################

        # scores = np.zeros((popsize))

        # for tick in range(ticks):
        while True:

            if self.sim:
                # delta T = 40 ms -> 25fps
                pygame.time.delay(40 * play)        

                # reset screen
                self.win.fill(cb)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()

            ##############
            ### NN IOs ###
            ##############

            # # normalized distance from A to center, [-1, 1]
            # center_dist = (a0 - r1[0]) / rdx - 1
            # # normalized unit distances from A to B, [-1, 1]
            # ball_dx = (float(b0) - a0) / ra
            # ball_dy = (float(b1) - a1) / ra
            # # horizontal velocity of A / 100
            # horizontal_vel = float(vax) / 100
            # # angular velocity
            # angular_vel = float(o0) / np.pi


            # all [0,1] or close
            # normalized distance from A to center, [-1, 1]
            center_dist = (a0 - r1[0]) / rdx - 1

            center_dist_pos = float(center_dist>0)
            center_dist_neg = float(center_dist<0)
            center_dist = np.abs(center_dist)
            # normalized unit distances from A to B, [-1, 1]
            ball_dx = (float(b0) - a0) / ra

            ball_dx_pos = ball_dx>0
            ball_dx_neg = ball_dx<0
            ball_dx = np.abs(ball_dx)
            ball_dy = (a1 - float(b1) + 75) / ra
            # horizontal velocity of A / 100
            horizontal_vel = float(vax) / 100

            vax_pos = horizontal_vel>0
            vax_neg = horizontal_vel<0
            horizontal_vel = np.abs(horizontal_vel)
            # angular velocity
            angular_vel = float(o0) / np.pi

            angular_vel_pos = angular_vel>0
            angular_vel_neg = angular_vel<0
            angular_vel = np.abs(angular_vel)

            param_idx = 0


            #################################
            ### input/NN response updates ###
            #################################
            if play:
                g, fr, fj, fw = menu.update()
            if not nn:
                keys = pygame.key.get_pressed()
                left = keys[pygame.K_LEFT]
                right = keys[pygame.K_RIGHT]
            else:
                # inputs = np.array([[center_dist,
                #                             ball_dy,
                #                             ball_dx,
                #                             horizontal_vel,
                #                             angular_vel]])
                inputs = np.array([[center_dist,
                                        center_dist_pos,
                                        center_dist_neg,
                                        ball_dx,
                                        ball_dx_pos,
                                        ball_dx_neg,
                                        ball_dy,
                                        horizontal_vel,
                                        vax_pos,
                                        vax_neg,
                                        angular_vel,
                                        angular_vel_pos,
                                        angular_vel_neg]])

                out = self.model.pred(inputs)
                left = out==0
                right = out==1

            if left and right:
                pass
            elif left:
                vax -= vd
                dv = -vd
            elif right:
                vax += vd
                dv = vd
            # decelerate if no keys pressed
            else:
                if vax >= fr:
                    vax -= fr
                    dv = -fr
                elif vax <= -fr:
                    vax += fr
                    dv = fr
                else:
                    vax = 0
                    dv = 0

            ########################
            ### position updates ###
            ########################

            # check boundary conditions for A and update
            if vax < 0 and a0 + vax <= r1[0]:
                a0 = int(r1[0])
                dv = -vax
                vax = int(-fw * vax)
                dv += vax 
            elif vax > 0 and a0 + vax >= r2[0]:
                a0 = r2[0]
                dv = -vax
                vax = int(-fw * vax)
                dv += vax 
            else:
                a0 += vax
            # update B
            b0 = a0 - int(ra * np.cos(o0))
            b1 = a1 - int(ra * np.sin(o0))

            #######################
            ### angular updates ###
            #######################

            dv *= adv
            do = fj * do + np.arctan2(g * np.cos(o0), ra) - dv * np.sin(o0)
            o0 += do

            ######################
            ### pygame updates ###
            ######################

            # update B
            b0 = a0 - int(ra * np.cos(o0))
            b1 = a1 - int(ra * np.sin(o0))

            if self.sim:
                # fitness
                self.win.blit(self.font.render(f'fitness={int(fitness)}', True, (0,255,0)), fitness_loc)
                # rail
                pygame.draw.line(self.win, clg, r1, r2, 3)
                # a
                pygame.draw.circle(self.win, cdg, (int(a0), a1), rb)
                # b
                pygame.draw.circle(self.win, cdg, (int(b0), b1), rb)
                # # arm
                pygame.draw.line(self.win, cdg, (a0, a1), (b0, b1), 5)

                pygame.display.update() 

            # fitness += a1-b1+np.exp((a1-b1)/25)
            fitness += np.exp((a1-b1+150)/55)
            if not play:
                ticks -= 1
                if not ticks:
                    return fitness
