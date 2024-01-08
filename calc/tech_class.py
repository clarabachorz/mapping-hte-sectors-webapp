# tech class
# can be used to generate tech objects, which have some basic properties


class tech:
    common_dict = dict()

    def __init__(self, init_dict, comp = False, ccu_income = False):
        self.init_dict = init_dict

        self.LCO_comps = {}

        # define some default values for LCO calculations, in case user does not explicitely define them
        self.wacc = 0.1
        self.flh = 0.9
        self.lifetime = 20

        # initiate the feedstock demand dictionnary
        self.feedstock_demand = {}
        # initiate allowed attribute list
        # If the user inputs anything outside this set in the json file, an error will be raised
        self.allowed_attr = set(
            {
                "key",
                "unit",
                "desc",
                "LCO",
                "capex",
                "opex",
                "othercosts",
                "flh",
                "wacc",
                "lifetime",
                "co2em",
                "co2capt",
                "compensation",
                "recycledco2",
                "offgrid",
                "co2ccusupply",
                "co2ccuincome"
            }
        )
        self.set_attr()
        
        self.check_offgrid()
        self.check_comp(comp)
        self.check_ccuincome(ccu_income)

        self.append_dict()


    def set_attr(self):
        for k, v in self.init_dict.items():
            try:
                self.add_attr(k, v)
            except KeyError as e:
                try:
                    self.add_feedstock_cost(k, v)
                except ValueError:
                    raise e from None
    # dictionnary used to store cost, emission and electricity usage data
    def get_dict(self):
        return self.common_dict

    def append_dict(self):
        self.common_dict[self.key] = [
            self.get_LCO(),
            self.get_eff_em(),
            self.get_eff_elec(),
            self.desc,
            self.get_total_co2dem(),
            self.get_total_em() -self.get_eff_em()
        ]

    def add_attr(_self, k, v):
        # check if the input attribute is allowed
        if k in _self.allowed_attr:
            setattr(_self, k, v)
        else:
            # raise error here
            raise KeyError(
                f'key "{k}" is not in expected list of attributes: {_self.allowed_attr}'
            )
        
    def add_feedstock_cost(self, k, v):
        # this function builds the feedstock demand dict

        # line below raises an error if the key k is not a demand type variable
        x = k.index("demand")
        # if it is indeed a feedstock, append to the class dict
        self.feedstock_demand[k[:x]] = v
        
    def check_offgrid(self):
        try:
            if self.offgrid:
                #special case: if offgrid is True, then we use electricity off grid rather than normal electricity
                self.feedstock_demand["elecoffgrid"] = self.feedstock_demand.pop("elec")
        except:
            pass

    def check_comp(self, comp):
        try:
            if comp:
                if any(sector in self.key for sector in ['chem','plane','ship','cement','steel']) and not "fossil" in self.key:
                    self.compensation = True
        except:
            pass

    def check_ccuincome(self, ccu_income):
        try:
            if ccu_income:
                if any(sector in self.key for sector in ['chem','plane','ship','cement','steel']) and not "fossil" in self.key:
                    self.co2ccuincome = True
        except:
            pass

    def get_LCO(self):
        # returns the LCO if already defined, otherwise calculates the value
        try:
            self.LCO_comps["tech"] = self.key
            self.LCO_comps["LCO"] = self.LCO
            return self.LCO
        except:
            self.LCO_comps["tech"] = self.key

            self.LCO = (
                self.LCOX_wo_energy()
                + self.get_other_costs()
                + self.get_total_feedstock_costs()
                + self.get_carbon_tax()
                + self.get_co2_storage_cost()
                + self.get_comp_cost()
                + self.get_ccu_income()
            )
            self.LCO_comps["LCO"] = self.LCO
            return self.LCO

    def get_total_feedstock_costs(self):
        feedstock_costs = 0

        for key in self.feedstock_demand.keys():
            feedstock_costs += self.get_feedstock_cost(key)
        return feedstock_costs


    def get_eff_em(self):
        # recycled_co2 = self.get_recycled_co2()

        try:
            if self.compensation:
                try:
                    if self.offgrid:
                        raise Exception("Compensation and offgrid electricity at the same time are not supported by current code version")
                except:
                    # if compensation is on, all emissions are compensated. Effective emissions are 0
                    # unless electricity has associated co2 emissions:
                    # be careful! compensation cannot operate with offgrid electricity in this current version
                    return (self.get_eff_elec() * self.common_dict["elec"][1])
        except:
            return self.get_total_em()

    def get_eff_elec(self):
        try:
            if self.compensation:
                # if compensation is on, need to add the additional electricity demand from DAC to total elec demand.
                return self.get_total_elec() + (
                    self.get_total_em() * self.common_dict["co2"][2]
                )
        except:
            return self.get_total_elec()

        
    def anf(self):
        anf = (self.wacc * (1 + self.wacc) ** self.lifetime) / (
            (1 + self.wacc) ** self.lifetime - 1
        )
        return anf

    def LCOX_wo_energy(self):
        # here, opex given in %
        try:
            ann_capex = self.capex * self.anf()
        except:
            ann_capex = 0
        
        try:
            fix_opex = self.opex * self.capex / 100
        except:
            fix_opex = 0
        
        ##issue here because of the return 0, which stops it from returning the LCO
        LCO_noenergy = (ann_capex + fix_opex) / self.flh
        
        self.LCO_comps["capex"] = ann_capex / self.flh
        self.LCO_comps["opex"] = fix_opex / self.flh

        return LCO_noenergy


    def get_total_em(self):
        total_em = self.get_em() - self.get_co2_capt() - self.get_co2_ccu()

        for key in self.feedstock_demand.keys():
            total_em += self.get_feedstock_em(key)
        
        #remove co2 fraction from plastics that are not actually combusted (for chemical feedstocks)
        #this amount is either recycled, or stored in a landfill
        total_em -= self.get_noncombustedplastic_co2(total_em) 
        return total_em
    
    def get_total_elec(self):
        total_elec = 0
        for key in self.feedstock_demand.keys():
            total_elec += self.get_elec_dem(key)
        return total_elec
    
    def get_total_co2dem(self):
        total_co2dem = self.get_co2dem()

        for key in self.feedstock_demand.keys():
            total_co2dem += self.get_feedstock_co2dem(key)

        return(total_co2dem)

    def get_carbon_tax(self):
        # TO CHANGE
        # for now self.get_total_em returns emissions even when compensation is True. Need to decide whether we need another function.
        # but until then, compensation route doesnt pay the carbon tax.
        try:
            if self.compensation:
                return 0
        except:
            try:
                self.LCO_comps["co2 tax"] = self.get_total_em() * self.common_dict["co2tax"][0]
                return self.get_total_em() * self.common_dict["co2tax"][0]
            except:
                return 0

    def get_co2_storage_cost(self):
        # we call this ccs, but really it is only storage and transport
        try:
            self.LCO_comps["co2 transport and storage"] = self.co2capt * self.common_dict["co2ts"][0]
            return self.co2capt * self.common_dict["co2ts"][0]
        except:
            return 0

    def get_comp_cost(self):
        # check if compensation has been set to True
        # adds the cost of compensating: DAC + Co2 storage and transport
        # also adds the amount of electricity required from DACCS
        try:
            if self.compensation:
                # returns compensation cost (cost of dac + cost of co2ts)

                self.LCO_comps["co2"] =self.get_total_em() * self.common_dict["co2"][0]
                self.LCO_comps["co2 transport and storage"] = self.get_total_em() * self.common_dict["co2ts"][0]
                return self.get_total_em() * (
                    self.common_dict["co2"][0] + self.common_dict["co2ts"][0]
                )
        except:
            return 0
        
    def get_ccu_income(self):
        #if co2 for ccu is obtained, it is sold at the co2ccu cost. This income has to be taken into account
        try:
            if self.co2ccuincome:
                return -self.co2ccusupply * self.common_dict["co2ccu"][0]
            else:
                return 0
        except:
            return 0

    def get_other_costs(self):
        try:
            self.LCO_comps["other costs"] = self.othercosts
            return self.othercosts
        except:
            return 0

    def get_em(self):
        try:
            return self.co2em
        except:
            return 0

    def get_co2_capt(self):
        try:
            return self.co2capt
        except:
            return 0
    
    def get_co2_ccu(self):
        #calculates co2 emissions from ccu that are taken in charge by the co2 ccu user (co2 from ccu * x, x the attribution for the user)
        try:
            return self.co2ccusupply * self.common_dict["co2ccu"][1]
        except:
            return 0

    def get_co2dem(self):
        #at the moment, only take into account dac co2. Not co2 from ccu
        try:
            return self.feedstock_demand["co2"]
        except:
            return 0
    
    def get_feedstock_cost(self, key):
        try:
            self.LCO_comps[key] = self.feedstock_demand[key] * self.common_dict[key][0]
            return self.feedstock_demand[key] * self.common_dict[key][0]
        except:
            return 0

    def get_feedstock_em(self, key):
        try:
            return self.feedstock_demand[key] * self.common_dict[key][1]
        except:
            return 0
    
    def get_elec_dem(self, key):
        try:
            if key == "elec" or key == "elecoffgrid":
                return self.feedstock_demand[key] * 1
            else:
                return self.feedstock_demand[key] * self.common_dict[key][2]
        except:
            return 0
    
    def get_feedstock_co2dem(self, key):
        try:
            return self.feedstock_demand[key] * self.common_dict[key][4]
        except:
            return 0
               

    def get_noncombustedplastic_co2(self, total_em):
        #DO I NEED THIS ?
        try:
            return(self.recycledco2)
        except:
            return 0

    ## NOT USED FOR NOW
    # def set_attr(_self, **kwargs):
    #     # s = set({"capex", "opex", "othercosts", "flh", "wacc", "lifetime", "co2em","_demand"})
    #     for k, v in kwargs.items():
    #         try:
    #             _self.add_attr(k, v)
    #         except KeyError as e:
    #             try:
    #                 _self.add_feedstock_cost(k, v)
    #             except ValueError:
    #                 raise e from None

    #     _self.get_LCO()
