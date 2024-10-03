import pickle
sam_scr=pickle.load(open('C:/git_hub/samplicity/sam_scr.p', "rb"))
def f_solve_asset_alloc(sam_scr):
    """ Function to solve the allocation of assets to the different portfolios. """

    # GEt the name of the division that can be used to allocate assets
    asset_div='div_e'

    # The first step is to get the SCR calculation
    scr_net=sam_scr.f_data('scr','scr','net')
    scr_net['assets','liabilities','net_assets','cover_ratio']=0
    scr_net['net_assets']=scr_net['assets']-scr_net['liabilities']
    scr_net['cover_ratio']=scr_net['net_assets']/scr_net['scr']

    div=sam_scr.output['diversification']['net'].copy(deep=True)
    div['assets','liabilities','net_assets','cover_ratio']=0
    div['assets']=div['scr']*1.12
    div['net_assets']=div['assets']-div['liabilities']
    div['cover_ratio']=div['net_assets']/div['scr']

    # We try a calcualtion, if there is an error we assume no imapct
    denominator = div.loc['div_e','assets']
    base_market_charge = div.loc['div_e','market'] / denominator if denominator != 0 else 0

    # Get teh additional assets we need for the divisions
    cover_ratio=sam_scr.f_data('data','data','division_detail')['scr_cover_ratio']
    required_assets=cover_ratio*div['scr']-div['assets']

    