/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
/* eslint camelcase: 0 react/jsx-filename-extension: 0 */
import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Grid, Row, Col, Alert } from 'react-bootstrap';
// import URI from 'urijs';
import { createMuiTheme } from '@material-ui/core/styles';
import { ThemeProvider } from '@material-ui/styles';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import SolarStepper from './SolarStepper';
import LocationSearchBox from './LocationSearchBox';
import DemoBox from './DemoBox';
import { Map, Marker, Circle, InfoWindow, GoogleApiWrapper } from '../../visualizations/SolarBI/google_maps_react';
import { fetchSolarData } from '../actions/solarActions';
import SaveModal from './SaveModal';
import CloseButton from './CloseButton';
import InfoTabs from './InfoTabs';
import HeatMap from './HeatMap';
import BarChart from './BarChart';
// import SolarCharts from './SolarCharts';
// import WelcomePage from './WelcomePage';
import DemoPage from './DemoPage';
import Loading from './Loading';

const theme = createMuiTheme({
  typography: {
    useNextVariants: true,
  },
  palette: {
    primary: {
      main: '#0063B0',
    },
    secondary: {
      main: '#0063B0',
    },
  },

});

const propTypes = {
  solarBI: PropTypes.object.isRequired,
  fetchSolarData: PropTypes.func.isRequired,
  // width: PropTypes.string.isRequired,
  google: PropTypes.object.isRequired,
};

export class MapView extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      center: {
        lat: -37.8136276,
        lng: 144.96305759999996,
      },
      radius: 3.5,
      datasource_id: '',
      datasource_type: '',
      zoom: 13,
      address: '',
      options: {},
      showSaveModal: false,
      // showExportModal: false,
      can_save: false,
      searching: true,
      showingMap: false,
      activeMarker: {},
      selectedPlace: {},
      showingInfoWindow: false,
      showingEmptyAlert: false,
      showingWrongAlert: false,
    };

    this.onPlaceChanged = this.onPlaceChanged.bind(this);
    this.onGoBackClick = this.onGoBackClick.bind(this);
    this.requestData = this.requestData.bind(this);
    this.toggleSaveModal = this.toggleSaveModal.bind(this);
    // this.toggleExportModal = this.toggleExportModal.bind(this);
    this.getFormData = this.getFormData.bind(this);
    // this.getCSVURL = this.getCSVURL.bind(this);
    this.onMarkerClick = this.onMarkerClick.bind(this);
    this.onInfoWindowClose = this.onInfoWindowClose.bind(this);
    this.onMapClicked = this.onMapClicked.bind(this);
    this.handleEmptyErrorAlert = this.handleEmptyErrorAlert.bind(this);
    this.handleWrongErrorAlert = this.handleWrongErrorAlert.bind(this);
  }

  componentDidMount() {
    const { solarBI } = this.props;
    const { form_data } = solarBI;
    if (
      solarBI.hasOwnProperty('form_data') &&
      form_data.hasOwnProperty('spatial_address')
    ) {
      // eslint-disable-next-line react/no-did-mount-set-state
      this.setState(
        {
          center: {
            lat: form_data.spatial_address.lat,
            lng: form_data.spatial_address.lon,
          },
          radius: form_data.radius,
          address: form_data.spatial_address.address,
          showingMap: true,
          searching: false,
          datasource_id: solarBI.datasource_id,
          datasource_type: solarBI.datasource_type,
          solar_new: false,
          can_save: false,
          can_export: false,
        },
        function () {
          this.requestData();
        },
      );
    } else {
      // eslint-disable-next-line react/no-did-mount-set-state
      this.setState({
        // data_source: form_data["datasource"],
        datasource_id: solarBI.datasource_id,
        datasource_type: solarBI.datasource_type,
        solar_new: true,
        can_save: false,
        can_export: false,
      });
    }
  }

  onPlaceChanged(place) {
    if (place && place.geometry) {
      const lat = place.geometry.location.lat.call();
      const lng = place.geometry.location.lng.call();
      this.setState(
        {
          address: place.formatted_address,
          center: {
            lat,
            lng,
          },
          zoom: 13,
          searching: false,
          showingMap: true,
        },
        function () {
          this.requestData();
        },
      );
    } else if (place === '') {
      this.handleEmptyErrorAlert();
    } else {
      this.handleWrongErrorAlert();
    }
  }

  onGoBackClick(gotodash) {
    if (gotodash) {
      window.location = '/solar/list';
    } else {
      this.setState({
        searching: true,
        showingMap: false,
        can_save: false,
        can_export: false,
      });
    }
  }

  onMarkerClick(props, marker) {
    this.setState({
      activeMarker: marker,
      selectedPlace: props,
      showingInfoWindow: true,
    });
  }

  onInfoWindowClose() {
    this.setState({
      activeMarker: {},
      showingInfoWindow: false,
    });
  }

  onMapClicked() {
    if (this.state.showingInfoWindow) {
      this.setState({
        activeMarker: {},
        showingInfoWindow: false,
      });
    }
  }

  getFormData() {
    return {
      datasource_id: this.state.datasource_id,
      datasource_type: this.state.datasource_type,
      viz_type: 'solarBI',
      radius: this.state.radius,
      spatial_address: {
        address: this.state.address,
        lat: this.state.center.lat,
        lon: this.state.center.lng,
        latCol: 'longitude',
        lonCol: 'latitude',
        type: 'latlong',
      },
    };
  }

  // getCSVURL() {
  //   const formData = this.getFormData();
  //   const uri = new URI('/');
  //   const directory =
  //     '/superset/explore_json/' +
  //     formData.datasource_type +
  //     '/' +
  //     formData.datasource_id +
  //     '/';
  //   const search = uri.search(true);
  //   search.form_data = JSON.stringify(formData);
  //   search.standalone = 'true';
  //   search.csv = 'true';
  //   const part_uri = uri
  //     .directory(directory)
  //     .search(search)
  //     .toString();
  //   return window.location.origin + part_uri + `&height=${this.state.height}`;
  // }
  requestData() {
    const formData = this.getFormData();
    this.props.fetchSolarData(formData, false, 60, '');
  }

  handleWrongErrorAlert() {
    this.setState({
      showingWrongAlert: true,
    });

    setTimeout(() => {
      this.setState({
        showingWrongAlert: false,
      });
    }, 3000);
  }

  handleEmptyErrorAlert() {
    this.setState({
      showingEmptyAlert: true,
    });

    setTimeout(() => {
      this.setState({
        showingEmptyAlert: false,
      });
    }, 3000);
  }

  toggleSaveModal() {
    this.setState({ showSaveModal: !this.state.showSaveModal });
  }

  // toggleExportModal() {
  //   this.setState({ showExportModal: !this.state.showExportModal });
  // }


  render() {
    const { entry } = this.props.solarBI;
    let reactEcharts = null;
    let closestMarker = null;
    let infoWindow = null;
    const { solarStatus, queryResponse, solarAlert } = this.props.solarBI;
    if (solarStatus === 'success' && queryResponse) {
      const closestPoint = {
        lat: queryResponse.data.lat,
        lng: queryResponse.data.lng,
      };
      closestMarker = (
        <Marker
          position={closestPoint}
          name="Nearest Data Collection Point"
          onClick={this.onMarkerClick}
          icon={{
            url:
              'https://i.ibb.co/d58fhn1/red-marker.png',
          }}
        />
      );
      infoWindow = (
        <InfoWindow
          marker={this.state.activeMarker}
          onClose={this.onInfoWindowClose}
          visible={this.state.showingInfoWindow}
        >
          <div>
            <p
              style={{
                fontFamily: 'Helvetica,Arial,sans-serif',
                margin: 'auto',
              }}
            >
              {this.state.selectedPlace.name}
            </p>
          </div>
        </InfoWindow>
      );
      reactEcharts = (
        <div>
          <InfoTabs
            address={this.state.address}
            onBackClick={this.onGoBackClick}
            onSaveClick={this.toggleSaveModal}
            // onExportClick={this.toggleExportModal}
            // getCSVURL={this.getCSVURL}
            can_save={this.props.solarBI.can_save}
            can_export={this.props.solarBI.can_export}
            solar_new={this.state.solar_new}
          />
        </div>
      );
    } else if (solarStatus === 'loading') {
      reactEcharts = (<Loading size={80} />);
    } else if (solarStatus === 'failed') {
      reactEcharts = (
        <Alert bsStyle="danger">
          <p style={{ textAlign: 'center' }}>
            <strong id="failAlert">{solarAlert}! Please try again!</strong>
          </p>
        </Alert>
      );
    }

    const defaultIcon = {
      url:
        'https://i.ibb.co/23Gypbr/green-marker.png',
      // scaledSize: new this.props.google.maps.Size(20, 30) // scaled size
    };

    return (
      <div>
        <ThemeProvider theme={theme}>
          {this.state.showingEmptyAlert && (
            <Grid style={{ position: 'absolute', top: 0 }}>
              <Row className="show-grid" xs={12}>
                <Col>
                  <Alert bsStyle="danger" style={{ margin: 'auto' }}>
                    Please Enter An Address
                  </Alert>
                </Col>
              </Row>
            </Grid>
          )}
          {this.state.showingWrongAlert && (
            <Grid style={{ position: 'absolute', top: 0 }}>
              <Row className="show-grid" xs={12}>
                <Col>
                  <Alert bsStyle="danger" style={{ margin: 'auto' }}>
                    Please Select An Address From The Pop-up Window
                  </Alert>
                </Col>
              </Row>
            </Grid>
          )}

          {/* {this.state.searching && entry === 'welcome' && (
            <div>
              <WelcomePage />
            </div>
          )} */}
          {this.state.searching && entry === 'demo' && (
            <div>
              <DemoPage />
            </div>
          )}
          {this.state.searching && entry !== 'welcome' && entry !== 'demo' && (
            <Grid>
              <div className="solar-stepper">
                <SolarStepper activeStep={0} />
              </div>
              <Row className="show-grid">
                <Col xs={10} xsOffset={1} md={10} mdOffset={1}>
                  <LocationSearchBox
                    address={this.state.address}
                    onPlaceChanged={place => this.onPlaceChanged(place)}
                  />
                  <DemoBox />
                </Col>
              </Row>
            </Grid>
          )}
          {this.state.showingMap && (
            <React.Fragment>
              <div style={{ padding: 0, width: 800, margin: 'auto' }}>
                <SolarStepper activeStep={1} />
              </div>
              <Card style={{ margin: '40px auto', width: '93%', height: 850 }}>
                <CardContent>
                  <CloseButton
                    onBackClick={this.onGoBackClick}
                    solar_new={this.state.solar_new}
                    saveStatus={this.props.solarBI.saveStatus}
                  />
                  <Grid>
                    <Row className="show-grid">
                      <Col xsOffset={1} xs={10} md={12} mdOffset={0}>
                        {this.state.showingMap && (
                          <div style={{ marginRight: 75 }}>
                            {!this.state.solar_new ?
                              <p
                                style={{
                                  fontFamily: 'Open Sans, sans-serif',
                                  fontSize: 23,
                                  fontWeight: 500,
                                  textAlign: 'center',
                                  color: '024067',
                                }}
                              >
                                {this.props.solarBI.form_data.requestParams.slice_name}
                              </p> : null
                            }
                            <p
                              style={{
                                fontFamily: 'Open Sans, sans-serif',
                                fontSize: 21,
                                textAlign: 'center',
                                color: '024067',
                              }}
                            >
                              {this.state.address.slice(0, -11)}
                            </p>
                            <hr style={{ display: 'block', width: 159, height: 1, border: 0, borderTop: '1px solid #808495', margin: '1em auto 2em', padding: 0 }} />
                          </div>
                        )}
                        <div style={{ display: 'flex', marginLeft: 20 }}>
                          <Map
                            visible={this.state.showingMap && solarStatus === 'success' && queryResponse !== null}
                            google={this.props.google}
                            zoom={this.state.zoom}
                            onClick={this.onMapClicked}
                            initialCenter={this.state.center}
                            center={this.state.center}
                            style={{
                              boxShadow:
                                '0 1px 3px rgba(0,0,0,0.12), 0 4px 6px rgba(29,114,12,0.24)',
                              borderRadius: '1em',
                              height: '300px',
                              width: '100%',
                              position: 'relative',
                            }}
                          >
                            <Marker
                              position={this.state.center}
                              name={this.state.address}
                              icon={defaultIcon}
                              onClick={this.onMarkerClick}
                            />
                            {closestMarker}
                            {infoWindow}

                            <Circle
                              radius={this.state.radius * 1000}
                              center={this.state.center}
                              strokeColor="transparent"
                              strokeOpacity={0}
                              strokeWeight={5}
                              fillColor={'#FF0000'}
                              fillOpacity={0.2}
                            />
                          </Map>
                          {solarStatus === 'success' && queryResponse && <HeatMap queryData={queryResponse.data.data} />}
                        </div>
                        {solarStatus === 'success' && queryResponse && <BarChart queryData={queryResponse.data.data} />}
                        {reactEcharts}
                      </Col>
                    </Row>
                  </Grid>
                </CardContent>
              </Card>
            </React.Fragment>
          )}
          <SaveModal
            open={this.state.showSaveModal}
            onHide={this.toggleSaveModal}
            form_data={{
              datasource_id: this.state.datasource_id,
              datasource_type: this.state.datasource_type,
              viz_type: 'solarBI',
              radius: this.state.radius,
              spatial_address: {
                address: this.state.address,
                lat: this.state.center.lat,
                lon: this.state.center.lng,
                latCol: 'longitude',
                lonCol: 'latitude',
                type: 'latlong',
              },
            }}
            userId={''}
          />
        </ThemeProvider>
      </div>
    );
  }
}

MapView.propTypes = propTypes;

const mapStateToProps = state => ({
  solarBI: state.solarBI,
});

export default connect(
  mapStateToProps,
  { fetchSolarData },
)(
  GoogleApiWrapper({
    apiKey: 'AIzaSyAc65tB0eu0jqft4ip7De7VcD56BpYlgio',
  })(MapView),
);
