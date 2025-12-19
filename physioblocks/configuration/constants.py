# SPDX-FileCopyrightText: Copyright INRIA
#
# SPDX-License-Identifier: LGPL-3.0-only
#
# Copyright INRIA
#
# This file is part of PhysioBlocks, a library mostly developed by the
# [Ananke project-team](https://team.inria.fr/ananke) at INRIA.
#
# Authors:
# - Colin Drieu
# - Dominique Chapelle
# - François Kimmig
# - Philippe Moireau
#
# PhysioBlocks is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free Software
# Foundation, version 3 of the License.
#
# PhysioBlocks is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# PhysioBlocks. If not, see <https://www.gnu.org/licenses/>.

# Simulation

# Simulation item id in the configuration
SIMULATION_ID = "simulation"

# Boundary conditions item id in the configuration.
BOUNDARIES_ID = "boundaries_conditions"

# Parameters register id in the configuration
PARAMETERS_ID = "parameters"

# Definition of the flux-dof types couples
FLUX_DOF_DEFINITION_ID = "flux_dof_definitions"


# Magnitudes

# The variable magnitude item label in the configuration
MAGNITUDES = "magnitudes"

# The variable magnitude item label in the configuration
VARIABLES_MAGNITUDES = "variables_magnitudes"

# Nets

# Net label id in the configuration
NET_ID = "net"

# Label of the nodes item
NODES_ITEM_ID = "nodes"

# Blocks

# Label of the blocks item
BLOCKS_ITEM_ID = "blocks"

# Label of the flux type component in block definition.
BLOCK_FLUX_TYPE_ITEM_ID = "flux_type"

# Label of the submodels components item
SUBMODEL_ITEM_ID = "submodels"

# Label of the model type item
MODEL_COMPONENT_TYPE_ITEM_ID = "model_type"


# Boundary Conditions

# The id of the type of boundary condition field in the configuration
CONDITION_TYPE_ID = "condition_type"

# The id of the name of boundary condition field in the configuration
CONDITION_NAME_ID = "condition_id"


# Solvers

# The solver item label in the configuration
SOLVER_ID = "solver"

# Solver tolerance config id constant
TOLERANCE_VAL_ID = "tolerance"

# Solver maximum iteration config id constant
ITERATION_MAX_VAL_ID = "iteration_max"


# State

# Id of the initialization values of the variables in the configuration
INIT_VARIABLES_ID = "variables_initialization"


# Time Manager

# Time id in the configuration
TIME_MANAGER_ID = "time"

# End time of the simulation id in the configuration
TIME_DURATION_TIME_VAL_ID = "duration"

# Start time of the simulation id in the configuration
TIME_START_TIME_VAL_ID = "start"

# Time step id in the configuration
TIME_STEP_TIME_VAL_ID = "step_size"

# Minimum time step size id in the configuration
TIME_STEP_MIN_VAL_ID = "min_step"


# Outputs

# Optional field id for output functions in the simulation configuration.
OUTPUTS_FUNCTIONS_ID = "output_functions"
