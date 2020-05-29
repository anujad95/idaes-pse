##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2019, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Tests for generic reaction package core code

Author: Andrew Lee
"""
import pytest

from pyomo.environ import (
    Block, ConcreteModel, Constraint, Expression, exp, Set, Var, value)

from idaes.generic_models.properties.core.generic.generic_reaction import (
        GenericReactionParameterBlock)
from idaes.generic_models.properties.core.reactions.dh_rxn import \
    constant_dh_rxn
from idaes.generic_models.properties.core.reactions.rate_constant import \
    arrhenius
from idaes.generic_models.properties.core.reactions.rate_forms import \
    mole_frac_power_law_rate
from idaes.generic_models.properties.core.reactions.equilibrium_constant import \
    van_t_hoff
from idaes.generic_models.properties.core.reactions.equilibrium_forms import \
    mole_frac_power_law_equil

from idaes.core.util.testing import PhysicalParameterTestBlock
from idaes.core.util.constants import Constants as constants

from idaes.core.util.exceptions import ConfigurationError


class TestGenericReactionParameterBlock(object):
    def test_rate_build(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        m.rxn_params = GenericReactionParameterBlock(default={
            "property_package": m.params,
            "rate_reactions": {
                "r1": {"stoichiometry": {("p1", "c1"): -1,
                                         ("p1", "c2"): 2},
                       "heat_of_reaction": "foo",
                       "rate_form": "foo"}}})

        rxn_config = m.rxn_params.config.rate_reactions

        assert isinstance(m.rxn_params.rate_reaction_idx, Set)
        assert len(m.rxn_params.rate_reaction_idx) == 1
        assert "r1" in m.rxn_params.rate_reaction_idx

        assert not hasattr(self, "equilibrium_reaction_idx")

        assert isinstance(m.rxn_params.rate_reaction_stoichiometry, dict)
        assert len(m.rxn_params.rate_reaction_stoichiometry) == 4
        for k, v in m.rxn_params.rate_reaction_stoichiometry.items():
            if (k[1], k[2]) in rxn_config[k[0]].stoichiometry.keys():
                assert v == rxn_config[k[0]].stoichiometry[k[1], k[2]]
            else:
                assert v == 0

        assert not hasattr(self, "equilibrium_reaction_stoichiometry")

        assert isinstance(m.rxn_params.reaction_idx, Set)
        assert m.rxn_params.reaction_idx == m.rxn_params.rate_reaction_idx

        assert isinstance(m.rxn_params.reaction_r1, Block)

    def test_rate_build_no_stoichiometry(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params rate reaction r1 was not "
                           "provided with a stoichiometry configuration "
                           "argument."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "rate_reactions": {
                    "r1": {"heat_of_reaction": "foo",
                           "rate_form": "foo"}}})

    def test_rate_build_invalid_phase_stoichiometry(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params stoichiometry for rate reaction "
                           "r1 included unrecognised phase p7."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "rate_reactions": {
                    "r1": {"stoichiometry": {("p7", "c1"): -1,
                                             ("p1", "c2"): 2},
                           "heat_of_reaction": "foo",
                           "rate_form": "foo"}}})

    def test_rate_build_invalid_component_stoichiometry(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params stoichiometry for rate reaction "
                           "r1 included unrecognised component c7."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "rate_reactions": {
                    "r1": {"stoichiometry": {("p1", "c7"): -1,
                                             ("p1", "c2"): 2},
                           "heat_of_reaction": "foo",
                           "rate_form": "foo"}}})

    def test_rate_build_no_form(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params rate reaction r1 was not "
                           "provided with a rate_form configuration "
                           "argument."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "rate_reactions": {
                    "r1": {"stoichiometry": {("p1", "c1"): -1,
                                             ("p1", "c2"): 2},
                           "heat_of_reaction": "foo"}}})

    def test_equil_build(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        m.rxn_params = GenericReactionParameterBlock(default={
            "property_package": m.params,
            "equilibrium_reactions": {
                "e1": {"stoichiometry": {("p2", "c1"): -3,
                                         ("p2", "c2"): 4},
                       "heat_of_reaction": "foo",
                       "equilibrium_form": "foo"}}})

        rxn_config = m.rxn_params.config.equilibrium_reactions

        assert isinstance(m.rxn_params.equilibrium_reaction_idx, Set)
        assert len(m.rxn_params.equilibrium_reaction_idx) == 1
        assert "e1" in m.rxn_params.equilibrium_reaction_idx

        assert not hasattr(self, "rate_reaction_idx")

        assert isinstance(m.rxn_params.equilibrium_reaction_stoichiometry,
                          dict)
        assert len(m.rxn_params.equilibrium_reaction_stoichiometry) == 4
        for k, v in m.rxn_params.equilibrium_reaction_stoichiometry.items():
            if (k[1], k[2]) in rxn_config[k[0]].stoichiometry.keys():
                assert v == rxn_config[k[0]].stoichiometry[k[1], k[2]]
            else:
                assert v == 0

        assert not hasattr(self, "rate_reaction_stoichiometry")

        assert isinstance(m.rxn_params.reaction_idx, Set)
        assert m.rxn_params.reaction_idx == \
            m.rxn_params.equilibrium_reaction_idx

        assert isinstance(m.rxn_params.reaction_e1, Block)

    def test_equil_build_no_stoichiometry(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params equilibrium reaction e1 was not "
                           "provided with a stoichiometry configuration "
                           "argument."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "equilibrium_reactions": {
                    "e1": {"heat_of_reaction": "foo",
                           "equilibrium_form": "foo"}}})

    def test_equil_build_invalid_phase_stoichiometry(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params stoichiometry for equilibrium "
                           "reaction e1 included unrecognised phase p7."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "equilibrium_reactions": {
                    "e1": {"stoichiometry": {("p7", "c1"): -3,
                                             ("p2", "c2"): 4},
                           "heat_of_reaction": "foo",
                           "equilibrium_form": "foo"}}})

    def test_equil_build_invalid_component_stoichiometry(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params stoichiometry for equilibrium "
                           "reaction e1 included unrecognised component c7."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "equilibrium_reactions": {
                    "e1": {"stoichiometry": {("p2", "c7"): -3,
                                             ("p2", "c2"): 4},
                           "heat_of_reaction": "foo",
                           "equilibrium_form": "foo"}}})

    def test_equil_build_no_form(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        with pytest.raises(ConfigurationError,
                           match="rxn_params equilibrium reaction e1 was not "
                           "provided with a equilibrium_form configuration "
                           "argument."):
            m.rxn_params = GenericReactionParameterBlock(default={
                "property_package": m.params,
                "equilibrium_reactions": {
                    "e1": {"stoichiometry": {("p2", "c1"): -3,
                                             ("p2", "c2"): 4},
                           "heat_of_reaction": "foo"}}})

    def test_rate_and_equil_build(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        m.rxn_params = GenericReactionParameterBlock(default={
            "property_package": m.params,
            "rate_reactions": {
                "r1": {"stoichiometry": {("p1", "c1"): -1,
                                         ("p1", "c2"): 2},
                       "heat_of_reaction": "foo",
                       "rate_form": "foo"}},
            "equilibrium_reactions": {
                "e1": {"stoichiometry": {("p2", "c1"): -3,
                                         ("p2", "c2"): 4},
                       "heat_of_reaction": "foo",
                       "equilibrium_form": "foo"}}})

        r_rxn_config = m.rxn_params.config.rate_reactions

        assert isinstance(m.rxn_params.rate_reaction_idx, Set)
        assert len(m.rxn_params.rate_reaction_idx) == 1
        assert "r1" in m.rxn_params.rate_reaction_idx

        assert not hasattr(self, "equilibrium_reaction_idx")

        assert isinstance(m.rxn_params.rate_reaction_stoichiometry, dict)
        assert len(m.rxn_params.rate_reaction_stoichiometry) == 4
        for k, v in m.rxn_params.rate_reaction_stoichiometry.items():
            if (k[1], k[2]) in r_rxn_config[k[0]].stoichiometry.keys():
                assert v == r_rxn_config[k[0]].stoichiometry[k[1], k[2]]
            else:
                assert v == 0

        assert not hasattr(self, "equilibrium_reaction_stoichiometry")

        e_rxn_config = m.rxn_params.config.equilibrium_reactions

        assert isinstance(m.rxn_params.equilibrium_reaction_idx, Set)
        assert len(m.rxn_params.equilibrium_reaction_idx) == 1
        assert "e1" in m.rxn_params.equilibrium_reaction_idx

        assert not hasattr(self, "rate_reaction_idx")

        assert isinstance(m.rxn_params.equilibrium_reaction_stoichiometry,
                          dict)
        assert len(m.rxn_params.equilibrium_reaction_stoichiometry) == 4
        for k, v in m.rxn_params.equilibrium_reaction_stoichiometry.items():
            if (k[1], k[2]) in e_rxn_config[k[0]].stoichiometry.keys():
                assert v == e_rxn_config[k[0]].stoichiometry[k[1], k[2]]
            else:
                assert v == 0

        assert not hasattr(self, "rate_reaction_stoichiometry")

        assert isinstance(m.rxn_params.reaction_idx, Set)
        assert m.rxn_params.reaction_idx == (
            m.rxn_params.rate_reaction_idx |
            m.rxn_params.equilibrium_reaction_idx)
        assert len(m.rxn_params.reaction_idx) == 2

        assert isinstance(m.rxn_params.reaction_r1, Block)
        assert isinstance(m.rxn_params.reaction_e1, Block)

    def test_build_parameters(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()

        m.rxn_params = GenericReactionParameterBlock(default={
            "property_package": m.params,
            "rate_reactions": {
                "r1": {"stoichiometry": {("p1", "c1"): -1,
                                         ("p1", "c2"): 2},
                       "heat_of_reaction": constant_dh_rxn,
                       "rate_form": "foo",
                       "parameter_data": {
                           "dh_rxn_ref": -10000}}},
            "equilibrium_reactions": {
                "e1": {"stoichiometry": {("p2", "c1"): -3,
                                         ("p2", "c2"): 4},
                       "heat_of_reaction": constant_dh_rxn,
                       "equilibrium_form": "foo",
                       "parameter_data": {
                           "dh_rxn_ref": -20000}}}})

        assert isinstance(m.rxn_params.reaction_r1.dh_rxn_ref, Var)
        assert m.rxn_params.reaction_r1.dh_rxn_ref.fixed
        assert m.rxn_params.reaction_r1.dh_rxn_ref.value == -10000

        assert isinstance(m.rxn_params.reaction_e1.dh_rxn_ref, Var)
        assert m.rxn_params.reaction_e1.dh_rxn_ref.fixed
        assert m.rxn_params.reaction_e1.dh_rxn_ref.value == -20000


# -----------------------------------------------------------------------------
class TestGenericReactionBlock(object):
    @pytest.fixture
    def model(self):
        m = ConcreteModel()

        # Add a dummy thermo package for validation
        m.params = PhysicalParameterTestBlock()
        m.sblock = m.params.build_state_block([1])

        m.rxn_params = GenericReactionParameterBlock(default={
            "property_package": m.params,
            "rate_reactions": {
                "r1": {"stoichiometry": {("p1", "c1"): -1,
                                         ("p1", "c2"): 2},
                       "heat_of_reaction": constant_dh_rxn,
                       "rate_constant": arrhenius,
                       "rate_form": mole_frac_power_law_rate,
                       "parameter_data": {
                           "dh_rxn_ref": -10000,
                           "arrhenius_const": 1,
                           "energy_activation": 1000}}},
            "equilibrium_reactions": {
                "e1": {"stoichiometry": {("p2", "c1"): -3,
                                         ("p2", "c2"): 4},
                       "heat_of_reaction": constant_dh_rxn,
                       "equilibrium_constant": van_t_hoff,
                       "equilibrium_form": mole_frac_power_law_equil,
                       "parameter_data": {
                           "dh_rxn_ref": -20000,
                           "k_eq_ref": 100,
                           "T_eq_ref": 350}}}})

        m.rblock = m.rxn_params.build_reaction_block(
            [1], default={"state_block": m.sblock,
                          "has_equilibrium": True})

        return m

    def test_dh_rxn(self, model):
        assert isinstance(model.rxn_params.reaction_r1.dh_rxn_ref, Var)
        assert isinstance(model.rxn_params.reaction_e1.dh_rxn_ref, Var)
        assert model.rxn_params.reaction_r1.dh_rxn_ref.value == -10000
        assert model.rxn_params.reaction_e1.dh_rxn_ref.value == -20000

        assert isinstance(model.rblock[1].dh_rxn, Expression)
        assert len(model.rblock[1].dh_rxn) == 2
        assert value(model.rblock[1].dh_rxn["r1"]) == -10000
        assert value(model.rblock[1].dh_rxn["e1"]) == -20000

    def test_rate_constant(self, model):
        assert isinstance(model.rxn_params.reaction_r1.arrhenius_const, Var)
        assert model.rxn_params.reaction_r1.arrhenius_const.value == 1
        assert isinstance(model.rxn_params.reaction_r1.energy_activation, Var)
        assert model.rxn_params.reaction_r1.energy_activation.value == 1000

        assert isinstance(model.rblock[1].k_rxn, Expression)
        assert len(model.rblock[1].k_rxn) == 1
        assert value(model.rblock[1].k_rxn["r1"]) == value(
            1*exp(-1000/(constants.gas_constant*model.sblock[1].temperature)))

    def test_reaction_rate(self, model):
        rblk = model.rxn_params.reaction_r1
        assert isinstance(rblk.reaction_order, Var)
        assert len(rblk.reaction_order) == 4
        assert rblk.reaction_order["p1", "c1"].value == 1
        assert rblk.reaction_order["p1", "c2"].value == 0
        assert rblk.reaction_order["p2", "c1"].value == 0
        assert rblk.reaction_order["p2", "c2"].value == 0

        assert isinstance(model.rblock[1].reaction_rate, Expression)
        assert len(model.rblock[1].reaction_rate) == 1
        assert value(model.rblock[1].reaction_rate["r1"]) == value(
            model.rblock[1].k_rxn["r1"] *
            model.sblock[1].mole_frac_phase_comp["p1", "c1"]**1)

    def test_equilibrium_constant(self, model):
        assert isinstance(model.rxn_params.reaction_e1.k_eq_ref, Var)
        assert model.rxn_params.reaction_e1.k_eq_ref.value == 100
        assert isinstance(model.rxn_params.reaction_e1.T_eq_ref, Var)
        assert model.rxn_params.reaction_e1.T_eq_ref.value == 350

        assert isinstance(model.rblock[1].k_eq, Expression)
        assert len(model.rblock[1].k_eq) == 1
        assert value(model.rblock[1].k_eq["e1"]) == value(
            100*exp(-(-20000/constants.gas_constant) *
                    (1/model.sblock[1].temperature - 1/350)))

    def test_equilibrium_form(self, model):
        rblk = model.rxn_params.reaction_e1
        assert isinstance(rblk.reaction_order, Var)
        assert len(rblk.reaction_order) == 4
        assert rblk.reaction_order["p1", "c1"].value == 0
        assert rblk.reaction_order["p1", "c2"].value == 0
        assert rblk.reaction_order["p2", "c1"].value == -3
        assert rblk.reaction_order["p2", "c2"].value == 4

        assert isinstance(model.rblock[1].equilibrium_constraint, Constraint)
        assert len(model.rblock[1].equilibrium_constraint) == 1
        assert value(model.rblock[1].equilibrium_constraint["e1"].body) == \
            value(model.rblock[1].k_eq["e1"] -
                  model.sblock[1].mole_frac_phase_comp["p2", "c1"]**-3 *
                  model.sblock[1].mole_frac_phase_comp["p2", "c2"]**4)
