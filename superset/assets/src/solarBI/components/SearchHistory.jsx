import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import MaterialTable from 'material-table';

const propTypes = {
  solarBI: PropTypes.object.isRequired,
};

function SearchHistory({ solarBI }) {
  return (
    <MaterialTable
      title="Saved Searches"
      columns={[
        { title: 'SAVED NAME', field: 'name' },
        { title: 'ADDRESS', field: 'address' },
        { title: 'LAST DATE UPDATED', field: 'updateDate' },
      ]}
      data={[...solarBI.saved_queries]}
      style={{ width: '100%' }}
      options={{
        headerStyle: {
          backgroundColor: '#f6f9fc',
          color: '#8898aa',
        },
      }}
      onRowClick={(_event, rowData) => { window.location.href = rowData.slice_url; }}
    />
  );
}

SearchHistory.propTypes = propTypes;

const mapStateToProps = state => ({
  solarBI: state.solarBI,
});

export default connect(mapStateToProps)(SearchHistory);
