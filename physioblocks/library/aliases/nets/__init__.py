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

"""Nets aliases.

Aliases
-------

.. _alias_circulation_alone_net:

**circulation_alone_net**
    Aliases :class:`~.Net` (``net``) to describe a
    simple circulation model, useful to run tests.

    .. tikz:: Simple circulation model scheme
        :include: ../schemes/simple_circulation_model_heart.tex

    .. tikz:: Simple circulation model net
        :include: ../schemes/circulation_net_scheme_heart.tex

    The net defines the ``blood_flow`` and ``blood_pressure`` flux and DOF types
    (:ref:`heart_flux_dof_couples <alias_heart_flux_dof_couples>`), the
    ``aorta_proximal``, ``aorta_distal`` and ``venous`` nodes, and two
    :ref:`rc_block <alias_rc_block>` blocks.

    .. code-block:: json

        {
            "type": "circulation_alone_net",
            // Boundary conditions completing the net.
            "boundaries_conditions": {
                "aorta_proximal": ["<condition type>"],
                "venous": ["<condition type>"]
            }
        }

.. _alias_spherical_heart_net:

**spherical_heart_net**
    Aliases :class:`~.Net` (``net``) to describe a
    simple cardiovascular circulation model, with a spherical heart.

    .. tikz:: Spherical heart circulation model
        :include: ../schemes/model_heart_circulation_0D.tex

    .. tikz:: Spherical heart circulation net
        :include: ../schemes/spherical_heart_net_scheme.tex

    The net defines the ``blood_flow`` and ``blood_pressure`` flux and DOF types
    (:ref:`heart_flux_dof_couples <alias_heart_flux_dof_couples>`), the ``cavity``,
    ``atrial``, ``aorta_proximal``, ``aorta_distal`` and ``venous`` nodes, and the
    blocks:

    * ``cavity``: :ref:`spherical_cavity_block <alias_spherical_cavity_block>`.
    * ``valve_atrium`` and ``valve_arterial``:
      :ref:`valve_rl_block <alias_valve_rl_block>`.
    * ``capacitance_valve``: :ref:`c_block <alias_c_block>`.
    * ``circulation_aorta_proximal`` and ``circulation_aorta_distal``:
      :ref:`rc_block <alias_rc_block>`

    The alias renames the cavity's parameters:

    * ``cavity.radius``:  ``heart_radius``
    * ``cavity.thickness``: ``heart_thickness``
    * ``cavity.contractility``: ``heart_contractility``
    * ``cavity.external_pressure``: ``pleural.pressure``

    The backward conductance of both valve is initialized to the same id:
    ``conductance_iso``.

    The other quantities have default names ``<block_name>.<param_name>``.

    Without boundary condition, the state variables of the net are the blood pressures
    the nodes (``<node name>.blood_pressure``), the valves fluxes and the cavity
    submodels internal variables.

    .. code-block:: json

        {
            "type": "spherical_heart_net",
            // Boundary conditions completing the net.
            "boundaries_conditions": {
                "atrial": ["<condition type>"],
                "venous": ["<condition type>"]
            }
        }
"""
