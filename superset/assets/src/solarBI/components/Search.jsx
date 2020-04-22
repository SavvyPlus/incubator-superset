import React from 'react';
import PropTypes from 'prop-types';
import TopNav from './TopNav';
import LocationSearchBox from './LocationSearchBox';
import SearchHistory from './SearchHistory';

const propTypes = {
  address: PropTypes.string.isRequired,
  onPlaceChanged: PropTypes.func.isRequired,
};

function Search({ address, onPlaceChanged }) {
  return (
    <React.Fragment>
      <TopNav />
      <div className="header bg-primary pb-6">
        <div className="container-fluid">
          <div className="header-body">
            <div className="row py-4">
              <div className="col-lg-6 col-7">
                <nav aria-label="breadcrumb" className="d-none d-md-inline-block ml-md-4">
                  <ol className="breadcrumb breadcrumb-links breadcrumb-dark">
                    <li className="breadcrumb-item"><a href="#"><i className="fas fa-home" /></a></li>
                    <li className="breadcrumb-item"><a href="#">Search</a></li>
                  </ol>
                </nav>
              </div>
              <div className="col-lg-6 col-5 text-right"  >
                <div className="row">
                  <div className="col-xl-3 col-md-6">
                    <div className="card bg-gradient-primary border-0" />
                  </div>
                  <div className="col-xl-3 col-md-6">
                    <div className="card bg-gradient-info border-0" />
                  </div>
                  <div className="col-xl-3 col-md-6">
                    <div className="card bg-gradient-default border-0">

                      <div className="card-body">
                        <div className="row">
                          <div className="col">
                            <h5 className="card-title text-uppercase text-muted mb-0 text-white">Advance Request</h5>
                            <span className="h2 font-weight-bold mb-0 text-white">50/100</span>
                            <div className="progress progress-xs mt-3 mb-0">
                              <div className="progress-bar bg-success" role="progressbar" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100" style={{ width: '50%' }} />
                            </div>
                          </div>

                        </div>
                        <p className="mt-3 mb-0 text-sm">
                          <button type="button" className="btn btn-outline-success">Upgrade</button>
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="col-xl-3 col-md-6">
                    <div className="card bg-gradient-default border-0">

                      <div className="card-body">
                        <div className="row">
                          <div className="col">
                            <h5 className="card-title text-uppercase text-muted mb-0 text-white">Business Cases</h5>
                            <span className="h2 font-weight-bold mb-0 text-white">3/4</span>
                            <div className="progress progress-xs mt-3 mb-0">
                              <div className="progress-bar bg-success" role="progressbar" aria-valuenow="90" aria-valuemin="0" aria-valuemax="100" style={{ width: '75%' }} />
                            </div>
                          </div>

                        </div>
                        <p className="mt-3 mb-0 text-sm">
                          <button type="button" className="btn btn-outline-success">Buy More</button>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container-fluid mt--1">
        <div className="row">
          <div className="col-xl-12 mt--3">
            <div className="card-header ">
              <div className="row align-items-center">
                <LocationSearchBox
                  address={address}
                  onPlaceChanged={onPlaceChanged}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="container-fluid mt--0" style={{ marginTop: 50 }}>
        <div className="row">
          <div className="col-xl-12 mt--3">
            <div className="card-header ">
              <div className="row align-items-center">
                <SearchHistory />
              </div>
            </div>
          </div>
        </div>
      </div>
    </React.Fragment>
  );
}

Search.propTypes = propTypes;

export default Search;
