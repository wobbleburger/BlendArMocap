from abc import ABC
from dataclasses import dataclass
from enum import Enum

from .utils import constraints
from .utils.drivers import assignment
from ..utils import objects
from ...cgt_utils import m_V


class BpyRigging(ABC):
    # region constraints
    constraint_mapping = {
        "CAMERA_SOLVER": 0,
        "FOLLOW_TRACK": 1,
        "OBJECT_SOLVER": 2,
        "COPY_LOCATION": constraints.copy_location,
        "COPY_LOCATION_OFFSET": constraints.copy_location_offset,
        "COPY_ROTATION": constraints.copy_rotation,
        "COPY_ROTATION_WORLD": constraints.copy_rotation_world_space,
        "COPY_SCALE": 5,
        "COPY_TRANSFORMS": 6,
        "LIMIT_DISTANCE": 7,
        "LIMIT_LOCATION": 8,
        "LIMIT_ROTATION": 9,
        "LIMIT_SCALE": 10,
        "MAINTAIN_VOLUME": 11,
        "TRANSFORM": 12,
        "TRANSFORM_CACHE": 13,
        "CLAMP_TO": 14,
        "DAMPED_TRACK": constraints.damped_track,
        "IK": 16,
        "LOCKED_TRACK": 17,
        "SPLINE_IK": 18,
        "STRETCH_TO": 19,
        "TRACK_TO": 20,
        "ACTION": 21,
        "ARMATURE": 22,
        "CHILD_OF": 23,
        "FLOOR": 24,
        "FOLLOW_PATH": 25,
        "PIVOT": 26,
        "SHRINKWRAP": 27,
    }

    def add_constraint(self, bone, target, constraint):
        constraints = [c for c in bone.constraints]

        # overwriting constraint by
        # removing previously added constraints if types match
        print("adding constraints")
        for c in constraints:
            # setup correct syntax for comparison
            constraint_name = c.name
            print("applying constraint", constraint_name)
            if "_WORLD" in constraint_name:
                constraint_name.remove("_WORLD")
                print("world in name", constraint_name)
            elif "_OFFSET" in constraint_name:
                constraint_name.remove("_OFFSET", constraint_name)
            constraint_name = constraint_name.replace(" ", "_")
            constraint_name = constraint_name.upper()
            # remove match
            if constraint_name == constraint:
                bone.constraints.remove(c)

        try:
            # adding a new constraint
            m_constraint = bone.constraints.new(
                type=constraint
            )
            self.constraint_mapping[constraint](m_constraint, target)

        except TypeError:
            # call custom method with bone
            self.constraint_mapping[constraint](bone, target)

    # endregion

    # region driver
    def add_driver_batch(self, driver_target, driver_source, prop_source, prop_target,
                         data_path, func=None, target_rig=None):
        """ Add driver to object on x-y-z axis. """
        # check if custom prop has been added to the driver
        added = self.set_custom_property(driver_target, prop_target, True)

        if added is True:
            if func is None:
                func = ['', '', '']
            # attempt to add driver to all axis
            for i in range(3):
                assignment.add_driver(driver_target, driver_source, prop_source, prop_target,
                                      data_path[i], i, func[i], target_rig)
        else:
            print("Driver may not be applied to same target twice", driver_target.name)
    # endregion

    # region custom properties
    def set_custom_property(self, target_obj, prop_name, prop):
        if self.get_custom_property(target_obj, prop_name) == None:
            target_obj[prop_name] = prop
            return True
        else:
            return False

    @staticmethod
    def get_custom_property(target_obj, prop_name):
        try:
            value = target_obj[prop_name]
        except KeyError:
            value = None

        return value

    # endregion

    # region way to many lengths
    @staticmethod
    def get_location_offset(pose_bones, bone_name, target):
        # remove constraint before calc offset
        for constraint in pose_bones[bone_name].constraints:
            if constraint.type == "COPY_LOCATION":
                pose_bones[bone_name].constraints.remove(constraint)

        # calc offset
        bone_pos = pose_bones[bone_name].head
        ob = objects.get_object_by_name(target)
        tar = ob.location
        offset = bone_pos - tar

        return offset

    @staticmethod
    def get_location_offset_at_origin(pose_bones, bone_name, target, pivot_name):
        # remove constraint before calc offset
        for constraint in pose_bones[bone_name].constraints:
            if constraint.type == "COPY_LOCATION":
                pose_bones[bone_name].constraints.remove(constraint)

        # calc offset
        bone_pos = pose_bones[bone_name].head
        ob = objects.get_object_by_name(target)
        tar = ob.location
        offset = bone_pos
        return offset + tar

    def get_average_joint_empty_length(self, joint_empty_names):
        # get_empty_positions
        joints = []
        for joint_names in joint_empty_names:
            joint_locations = [objects.get_object_by_name(name).location for name in joint_names]
            joints.append(joint_locations)
        avg_dist = self.get_average_length(joints)
        return avg_dist

    @staticmethod
    def get_average_length(joint_array):
        distances = []
        for joint in joint_array:
            dist = m_V.get_vector_distance(joint[0], joint[1])
            distances.append(dist)
        avg_dist = sum(distances) / len(distances)
        return avg_dist

    @staticmethod
    def get_joint_length(joint):
        dist = m_V.get_vector_distance(joint[0], joint[1])
        return dist

    def get_average_joint_bone_length(self, joint_bone_names, pose_bones):
        """ requires an array of joints names [[bone_a, bone_b], []... ] and pose bones.
            returns the average length of the connected bones. """
        joints = self.get_joints(joint_bone_names, pose_bones)
        avg_dist = self.get_average_length(joints)
        return avg_dist

    @staticmethod
    def get_joints(joint_names, pose_bones):
        """ requires an array of joints names [[bone_a, bone_b], []... ] and pose bones.
        returns the bone head locations in the same formatting. """
        arm_joints = []
        for names in joint_names:

            joint = []
            for name in names:
                bone_pos = pose_bones[name].head
                joint.append(bone_pos)

            arm_joints.append(joint)
        return arm_joints
    # endregion


class DriverType(Enum):
    limb_driver = 0
    constraint = 1
    face_driver = 2


@dataclass(repr=True)
class MappingRelation:
    source: object
    values: list
    driver_type: Enum

    def __init__(self, source, driver_type: DriverType, *args):
        self.source = source
        self.driver_type = driver_type
        self.values = args
