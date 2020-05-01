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
import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import { withStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import GoBackModal from './GoBackModal';
import ExportModal from './ExportModal';

const styles = theme => ({
  disabled: {
    backgroundColor: 'lightgray',
  },
  exportBtn: {
    marginLeft: '40 !important',
    marginRight: '100 !important',
  },
  slider: {
    padding: '22px 0px',
  },
  card: {
    minWidth: 450,
  },
  infoBtn: {
    margin: '10 10',
    height: 40,
    padding: '0 16px',
    minWidth: 115,
    borderRadius: 60,
    color: 'white',
    backgroundColor: '#0063B0',
    border: 'none',
    fontSize: 16,
    fontFamily: 'Open Sans, sans-serif',
    fontWeight: 'bold',
    '&:hover': {
      color: 'white',
      backgroundColor: '#034980',
    },
    '&:focus': {
      outline: 'none',
    },
  },
  infoCard: {
    minHeight: 200,
    marginTop: 10,
    marginBottom: 100,
  },
  typography: {
    textAlign: 'center',
    marginTop: 10,
    marginBottom: 30,
  },
  icon: {
    color: '#09290f',
    backgroundColor: '#489795',
    transform: 'scale(1.4)',
    margin: '15 20',
  },
  saveBtn: {
    marginLeft: 50,
  },
  tooltip: {
    fontSize: 14,
  },
  tabContainer: {
    fontWeight: 300,
  },
  notUse: {
    margin: theme.spacing(1),
  },
});

class InfoTabs extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      tabValue: 0,
      showExportModal: false,
      showGoBackModal: false,
    };
    this.handleTabChange = this.handleTabChange.bind(this);
    this.onBackClick = this.onBackClick.bind(this);
    this.onSaveClick = this.onSaveClick.bind(this);
    this.toggleGoBackModal = this.toggleGoBackModal.bind(this);
    this.toggleExportModal = this.toggleExportModal.bind(this);
  }

  onBackClick() {
    if (this.props.can_save && this.props.solar_new) {
      this.props.onBackClick(false);
    } else {
      this.props.onBackClick(true);
    }
  }

  onSaveClick() {
    this.props.onSaveClick();
  }

  // getCSVURL() {
  //   return this.props.getCSVURL();
  // }

  toggleGoBackModal() {
    this.setState({ showGoBackModal: !this.state.showGoBackModal });
  }

  toggleExportModal() {
    this.setState({ showExportModal: !this.state.showExportModal });
  }

  handleTabChange(event, tabValue) {
    this.setState({ tabValue });
  }

  render() {
    // eslint-disable-next-line camelcase
    const { classes } = this.props;
    return (
      <div className={classes.root}>
        {/* <Tooltip title="Go Back" classes={{ tooltip: classes.tooltip }}>
          <IconButton
            id="backIcon"
            className={classes.icon}
            // eslint-disable-next-line camelcase
            onClick={solar_new ? this.toggleGoBackModal : this.onBackClick}
          >
            <KeyboardBackspaceIcon />
          </IconButton>
        </Tooltip> */}
        <div style={{ display: 'flex', float: 'right' }}>
          {this.props.can_save && this.props.solar_new && (
            <Button
              className={classNames(classes.infoBtn, classes.saveBtn)}
              onClick={this.onSaveClick}
            >
              Save
            </Button>
          )}
          {this.props.can_export && (
            <Button
              classes={{ disabled: classes.disabled }}
              className={classNames(classes.infoBtn, classes.exportBtn)}
              onClick={this.toggleExportModal}
            >
              Next
            </Button>
            // <Tooltip
            //   title="Export As CSV"
            //   classes={{ tooltip: classes.tooltip }}
            // >
            //   <IconButton
            //     id="exportIcon"
            //     className={classes.icon}
            //     // href={this.getCSVURL()}
            //     onClick={this.toggleExportModal}
            //   >
            //     <CloudDownloadIcon />
            //   </IconButton>
            // </Tooltip>
          )}
        </div>

        <ExportModal
          address={this.props.address}
          open={this.state.showExportModal}
          onHide={this.toggleExportModal}
          solar_new={this.props.solar_new}
        />
        <GoBackModal
          onBackClick={this.onBackClick}
          open={this.state.showGoBackModal}
          onClose={this.toggleGoBackModal}
        />
      </div>
    );
  }
}

InfoTabs.propTypes = {
  address: PropTypes.string.isRequired,
  classes: PropTypes.object.isRequired,
  onBackClick: PropTypes.func.isRequired,
  onSaveClick: PropTypes.func.isRequired,
  // getCSVURL: PropTypes.func.isRequired,
  can_save: PropTypes.bool.isRequired,
  can_export: PropTypes.bool.isRequired,
  solar_new: PropTypes.bool.isRequired,
};

export default withStyles(styles)(InfoTabs);
