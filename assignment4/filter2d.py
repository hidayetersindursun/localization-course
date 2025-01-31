from turtle import distance
from matplotlib.pyplot import sca
from numpy import mat
import scipy as sp
from torch import angle
from sim.plot2d import plot
import random as r
import math
import numpy as np


class Position:
    def __init__(self, pos):
        self.x = pos[0]
        self.y = pos[1]
        self.theta = pos[2]


class Pole(Position):
    def __init__(self, pos):
        Position.__init__(self, pos)


class Measurement:
    def __init__(self, distance, angle):
        self.distance = distance
        self.angle = angle


class Robot(Position):
    def __init__(self, pos):
        Position.__init__(self, pos)
        self.measurements = []
        self.max_measurement = 200

    # Movement is perfectly accurate, even though we are assuming it isn't.
    def move(self, speed, theta_dot):
        ### START STUDENT CODE
        self.theta += theta_dot
        self.x += math.cos(self.theta)*speed
        self.y += math.sin(self.theta)*speed
        ### END STUDENT CODE

    def move_with_error(self, speed, theta_dot):
        theta_dot = r.normalvariate(theta_dot, 0.2)
        speed = r.normalvariate(speed, 0.5)
        self.move(speed, theta_dot)

    # Measurement is perfectly accurate even though we are assuming it isn't.
    def measure(self, poles):
        ### START STUDENT CODE
        self.measurements = []
        for pole in poles:
            dist_y = pole.y - self.y
            dist_x = pole.x - self.x
            distance = math.sqrt(dist_y**2 + dist_x**2)
            if distance < self.max_measurement:
                angle = math.atan2(dist_y,dist_x)
                angle = angle - self.theta # robotun heading ine göre bi angle arıyoruz o yüzden self.theta dan çıkarttık.
            # Normalize angle : 0-2pi aralığına indirgiyoruz. 0.1 vs 2pi-0.1 are so close like 10 vs 350 degrees
                if angle > math.pi*2:
                    angle -= math.pi*2
                elif angle < -math.pi*2:
                    angle += math.pi*2
            
            self.measurements += [Measurement(distance,angle)]
        ### END STUDENT CODE


class Particle(Robot):
    def __init__(self, pos):
        Robot.__init__(self, pos)
        self.weight = 0.0
        self.distance_sigma = 5
        self.distance_distribution_peak = 1 / \
            (math.sqrt(2 * math.pi) * self.distance_sigma)
        self.distance_weight = 1
        self.angle_sigma = 0.5
        self.angle_distribution_peak = 1 / \
            (math.sqrt(2 * math.pi) * self.angle_sigma)
        self.angle_weight = 1
        self.theta_dot_sigma = 0.2
        self.speed_sigma = 0.5

    def predict(self, speed, theta_dot):
        ### START STUDENT CODE
        theta_dot = r.normalvariate(theta_dot,self.theta_dot_sigma) # normal distribution of theta_dot & theta_dot_sigma
        speed = r.normalvariate(speed,self.speed_sigma) # normal distribution of speed & speed_sigma
        self.move(speed,theta_dot)
        # return 0
        ### END STUDENT CODE

    def probability_density_function(self, mu, sigma, x):
        ### START STUDENT CODE
        pdf = (np.exp((((x - mu)/sigma)**2)*(-0.5)))/(sigma*np.sqrt(2*np.pi))
        return pdf
        ### END STUDENT CODE

    def update_weight(self, robot_measurements):
        ### START STUDENT CODE
        for p in self.measurements: # particle's measurements
            best_match = 0
            for r in robot_measurements: # robot's measurements
                distance_match = self.probability_density_function(r.distance, self.distance_sigma, p.distance)
                # normalize match   to 1 so we can treat distance and angle as equal weight
                distance_match = distance_match/self.distance_distribution_peak
                distance_match *= self.distance_weight
                
                # Need to use minimum angle
                # 10 vs 350 degrees = 20 degrees difference
                diff_angle = abs(p.angle-r.angle)
                if diff_angle > math.pi:
                    diff_angle = abs(diff_angle - math.pi*2)
                angle_match = self.probability_density_function(0, self.angle_sigma, diff_angle)
                angle_match = angle_match / self.angle_distribution_peak
                angle_match *= self.angle_weight
                # match ile aslında distance ve angle weightlerinden hangisini ne ölçüde kullancağımıza bakıyoruz.
                # match = distance_match + angle_match --> bu şekilde de yapabilirdik. biri kötü biri iyi olursa bu şekilde dengeler
                match = distance_match * angle_match #iki değer de iyi olmak zorunda, biri kötü olursa patlar.
                if match > best_match:
                    best_match = match
            self.weight += best_match
        # Normalize weights based on the number of poles within range.
        if len(robot_measurements) ==0:
            return 
        self.weight /= len(robot_measurements)
        #Square weight to give more resamples to the best particles.
        self.weight *= self.weight
        
        ### END STUDENT CODE


def resample_particles(particles):
    ### START STUDENT CODE
    num_particles = 100
    weights = []
    resampled_particles = []
    for particle in particles:
        weights += [particle.weight]
    resample = r.choices(range(num_particles),weights,k=num_particles)
    
    scale = len(particles) / (sum(weights)*5)
    if scale > 10:
        scale = 10
    if scale < 0.5:  # this is added for assignment 4-5, don't use in 4-4 !
        scale =0     # this is added for assignment 4-5, don't use in 4-4 !
    for i in resample:
        x = particles[i].x + r.normalvariate(0, particles[0].speed_sigma * scale)
        y = particles[i].y + r.normalvariate(0, particles[0].speed_sigma * scale)
        theta = particles[i].theta + r.normalvariate(0, particles[0].theta_dot_sigma * scale)
        resampled_particles += [Particle([x,y,theta])]
    
    return resampled_particles
    ### END STUDENT CODE
